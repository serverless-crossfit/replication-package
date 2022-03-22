from typing import List
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import pathlib
import seaborn as sns
import yaml
import logging
import sys
import os
# NOTE: Requires Python 3.10: https://docs.python.org/3/library/itertools.html#itertools.pairwise
from itertools import pairwise

# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# Configure paths
script_dir = pathlib.Path(__file__).parent.resolve()

## Input data directory
default_data_path = script_dir.parent / 'data'
data_path = default_data_path
if os.environ.get('DATA_PATH'):
    data_path = pathlib.Path(os.environ['DATA_PATH'])

## Output directory for plots
default_plots_path = script_dir / 'plots'
plots_path = default_plots_path
if os.environ.get('PLOTS_PATH'):
    plots_path = pathlib.Path(os.environ['PLOTS_PATH'])
else:
    plots_path.mkdir(exist_ok=True)

# Constants
TRACE_BREAKDOWN = 'trace_breakdown.csv'

date_cols = [
    't1',
    't2',
    't3',
    't4',
    't5',
    't6',
    't7',
    't8',
    't9',
    't10',
    't11',
    't12',
    't13'
]
timedelta_cols = [f"{col1}{col2}" for col1, col2 in pairwise(date_cols)] + ['total_duration']

# workload_type
label_mappings = {
    'experiment_non_bursty_1.py': 'C1',
    'experiment_non_bursty_2.py': 'C2',
    'experiment_non_bursty_3.py': 'C3',
    'experiment_bursty_1.py': 'B1',
    'experiment_bursty_2.py': 'B2',
    'experiment_bursty_3.py': 'B3'
}

provider_mappings = {
    'aws': 'AWS',
    'azure': 'Azure'
}

duration_mappings = {
    't1t2': 'TrigH',
    't2t3': 'InitF1',
    't3t4': 'CompF1',
    't4t5': 'AuthF1',
    't5t6': 'WriteF1',
    't6t7': 'TrigS',
    't7t8': 'InitF2',
    't8t9': 'AuthF2r',
    't9t10': 'ReadF2',
    't10t11': 'CompF2',
    't11t12': 'AuthF2w',
    't12t13': 'WriteF2',
    'total_duration': 'Total' # or E2E
}


# Import helper methods

def find_execution_paths(data_path) -> List[pathlib.Path]:
    "Returns a list of paths to log directories where 'trace_breakdown.csv' exists."
    # Execution log directories are in the datetime format 2021-04-30_01-09-33
    return [p.parent for p in pathlib.Path(data_path).rglob(TRACE_BREAKDOWN)]


def read_sb_app_config(execution):
    """Returns a dictionary with the parsed sb config from sb_config.yml"""
    config_path = execution / 'sb_config.yml'
    sb_config = {}
    app_config = {}
    app_name = ''
    if config_path.is_file():
        with open(config_path) as f:
            sb_config = yaml.load(f, Loader=yaml.FullLoader)
        app_name = list(sb_config.keys())[0]
        # Workaround for cases where sb is the first key
        if app_name == 'sb':
            app_name = list(sb_config.keys())[1]
        app_config = sb_config[app_name]
    else:
        logging.warning(f"Config file missing at {config_path}.")
        return dict()
    return app_config, app_name


def read_trace_breakdown(execution) -> pd.DataFrame:
    """Returns a pandas dataframe with the parsed trace_breakdown.csv"""
    trace_breakdown_path = pathlib.Path(execution) / TRACE_BREAKDOWN
    trace_breakdown = pd.read_csv(trace_breakdown_path, parse_dates=date_cols)
    return trace_breakdown


def filter_traces_warm(trace_breakdown) -> pd.DataFrame:
    traces = trace_breakdown[(trace_breakdown["f1_cold_start"] == 0) & (trace_breakdown["f2_cold_start"] == 0)]
    return traces


def string_to_datetime(str):
    return datetime.strptime(str, '%Y-%m-%d %H:%M:%S.%f')


def calculate_duration(x, y):
    diff = string_to_datetime(y) - string_to_datetime(x)
    diff_in_milliseconds = diff.total_seconds() * 1000
    return int(diff_in_milliseconds)


def calculate_toal_duration(x):
    diff = string_to_datetime(x['t13']) - string_to_datetime(x['t1'])
    diff_in_milliseconds = diff.total_seconds() * 1000
    return diff_in_milliseconds


def get_total_duration(trace_breakdown):
    """Returns a pandas dataframe with total duration for trace breakdowns"""
    trace_breakdown['total_duration'] = trace_breakdown.apply(calculate_toal_duration, axis=1)
    return trace_breakdown['total_duration'].to_numpy()


def get_total_duration_warm(trace_breakdown):
    """Returns a pandas dat daframe with total duration coming from warm invocations"""
    trace_breakdown['total_duration'] = trace_breakdown.apply(calculate_toal_duration, axis=1)
    new_trace_breakdown = trace_breakdown[(trace_breakdown["f1_cold_start"] == 0) & (trace_breakdown["f2_cold_start"] == 0)]
    return new_trace_breakdown['total_duration'].to_numpy()


def calculate_durations(trace_breakdown):
    "Adds timedelta columns with durations based on pairwise date comparison."
    # Fix SettingWithCopyWarning
    trace_breakdown = trace_breakdown.copy()
    for col1, col2 in pairwise(date_cols):
        trace_breakdown[f"{col1}{col2}"] = trace_breakdown[col2] - trace_breakdown[col1]
    # Add total duration (using diff of last - first date column)
    trace_breakdown['total_duration'] = trace_breakdown[date_cols[-1]] - trace_breakdown[date_cols[0]]
    return trace_breakdown


def get_selected_durations(trace_breakdown):
    """Returns a pandas dataframe with selected durations for trace breakdowns"""
    # NOTE: These non-vectorized operations are expected to perform slow with large datasets

    df = pd.DataFrame(columns=['duration_type', 'duration', 'provider', 'label'])

    i = 0
    for index, row in trace_breakdown.iterrows():

        i = i + 1

        df.loc[i, 'duration_type'] = 't₁t₂'
        df.loc[i, 'duration'] = calculate_duration(row['t1'], row['t2'])

        i = i + 1

        df.loc[i, 'duration_type'] = 't₂t₃'
        df.loc[i, 'duration'] = calculate_duration(row['t2'], row['t3'])

        i = i + 1

        df.loc[i, 'duration_type'] = 't₄t₅'
        df.loc[i, 'duration'] = calculate_duration(row['t4'], row['t5'])

        i = i + 1

        df.loc[i, 'duration_type'] = 't₅t₆'
        df.loc[i, 'duration'] = calculate_duration(row['t5'], row['t6'])

        i = i + 1

        df.loc[i, 'duration_type'] = 't₆t₇'
        df.loc[i, 'duration'] = calculate_duration(row['t6'], row['t7'])

        i = i + 1

        df.loc[i, 'duration_type'] = 't₇t₈'
        df.loc[i, 'duration'] = calculate_duration(row['t7'], row['t8'])

        i = i + 1

        df.loc[i, 'duration_type'] = 't₈t₉'
        df.loc[i, 'duration'] = calculate_duration(row['t8'], row['t9'])

        i = i + 1

        df.loc[i, 'duration_type'] = 't₉t₁₀'
        df.loc[i, 'duration'] = calculate_duration(row['t9'], row['t10'])

        i = i + 1

        df.loc[i, 'duration_type'] = 't₁₀t₁₁'
        df.loc[i, 'duration'] = calculate_duration(row['t10'], row['t11'])

        i = i + 1

        df.loc[i, 'duration_type'] = 't₁₁t₁₂'
        df.loc[i, 'duration'] = calculate_duration(row['t11'], row['t12'])

        i = i + 1

        df.loc[i, 'duration_type'] = 't₁₂t₁₃'
        df.loc[i, 'duration'] = calculate_duration(row['t12'], row['t13'])

        # Copy metadata from trace breakdowns
        df.loc[i, 'provider'] = row['provider']
        df.loc[i, 'label'] = row['label']

    # Solve error "ValueError: object arrays are not supported"
    df['duration'] = df['duration'].astype(str).astype(int)

    return df


def get_selected_durations_warm(trace_breakdown, provider):
    """Returns a pandas dataframe with selected durations for trace breakdowns with only warm invocations"""
    traces = filter_traces_warm(trace_breakdown)
    durations = get_selected_durations(traces, provider)
    return durations[durations['duration_type'] != 't₆t₇']
