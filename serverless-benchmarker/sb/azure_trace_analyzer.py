import logging
import json
from os import stat
import pandas as pd
import datetime
from pathlib import Path
from pandas.core.indexes.base import ensure_index


def ft(t) -> str:
    result = None
    try:
        result = datetime.datetime.strptime(t, '%Y-%m-%dT%H:%M:%S.%fZ')
    except ValueError:
        result = datetime.datetime.strptime(t, '%Y-%m-%dT%H:%M:%SZ')
    return result.strftime('%Y-%m-%d %H:%M:%S.%f')


class AzureTraceAnalyzer:
    """Parses traces.json files downloaded by the AzureTraceDownloader
    and saves a trace summary into trace_breakdown.csv
    """

    def __init__(self, log_path) -> None:
        self.log_path = log_path

    def analyze_traces(self):
        file = Path(self.log_path)
        breakdown_file = file.parent / 'trace_breakdown.csv'
        traces_file = file.parent / 'traces.json'

        # Clear traces data
        open(breakdown_file, 'w').close()

        # Using readline()
        file1 = open(traces_file, 'r')
        count = 0

        results = []
        while True:
            # Get next line from file
            line = file1.readline()

            # if line is empty
            # end of file is reached
            if not line:
                break

            data = json.loads(line)
            result = self.analyze_trace(data['traces'], data['trace_id'])
            results.append(result)
            count += 1

        result_df = pd.DataFrame(results)
        result_df.to_csv(breakdown_file, sep=',', index=False)

        file1.close()

        num_valid_traces = count

        logging.info(f"Analyzed {num_valid_traces} valid traces. Written to {breakdown_file.name}.")

    def time_diff_in_ms(self, start_time, end_time, format):

        start = None
        if type(start_time) is str:
            try:
                start = datetime.datetime.strptime(start_time, format)
            except ValueError:
                start = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")

        end = None
        if type(end_time) is str:
            try:
                end = datetime.datetime.strptime(end_time, format)
            except ValueError:
                end = datetime.datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%SZ")

        diff = end - start
        diff_ms = int(diff.total_seconds() * 1000)
        return diff_ms
    
    def strptime_pro(self, t, format):

        result = None
        try:
            result = datetime.datetime.strptime(t, format)
        except ValueError:
            result = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ")

        return result

    def analyze_trace(self, input_json, id):
        # Json string to json
        newjson = json.loads(input_json)
        df = pd.DataFrame.from_dict(newjson)

        time_format = "%Y-%m-%dT%H:%M:%S.%fZ"

        # Interesting time points
        t1 = df.loc[(df["itemType"]=="request") & (df["name"].str.contains("POST")), "timestamp"].values[0]
        t2 = df.loc[(df["itemType"]=="request") & (df["name"]=="Upload"), "timestamp"].values[0]
        t3 = df.loc[(df["name"]=="Upload function execution"), "timestamp"].values[0]
        t4 = df.loc[(df["itemType"]=="trace") & (df["message"].str.contains("Upload Blob Operation Starts")), "timestamp"].values[0]
        t5 = df.loc[(df["name"]=="PUT thumbnaistore") & (df["operation_Name"]=="Upload") & (df["resultCode"]== "201"), "timestamp"].values[0]
        t5_t6 = df.loc[(df["name"]=="PUT thumbnaistore") & (df["operation_Name"]=="Upload") & (df["resultCode"]== "201"), "duration"].values[0]
        t6 = (self.strptime_pro(t5, time_format) +  datetime.timedelta(milliseconds=t5_t6)).strftime(time_format)
        t7 = df.loc[(df["itemType"]=="request") & (df["name"]=="Create-Thumbnail"), "timestamp"].values[0]
        t8 = df.loc[(df["name"]=="CreateThumbnail execution"), "timestamp"].values[0]
        t9 = df.loc[(df["name"]=="GET thumbnaistore") & (df["operation_Name"]=="Create-Thumbnail"), "timestamp"].values[0]
        t9_t10 = df.loc[(df["name"]=="GET thumbnaistore") & (df["operation_Name"]=="Create-Thumbnail"), "duration"].values[0]
        t10 = (self.strptime_pro(t9, time_format) +  datetime.timedelta(milliseconds=t9_t10)).strftime(time_format)
        t11 = df.loc[(df["itemType"]=="trace") & (df["message"].str.contains("CreateThumbnail PUT Operation Starts")), "timestamp"].values[0]
        t12 = df.loc[(df["name"]=="PUT thumbnaistore") & (df["operation_Name"]=="Create-Thumbnail") & (df["resultCode"]== "201"), "timestamp"].values[0]
        t12_t13 = df.loc[(df["name"]=="PUT thumbnaistore") & (df["operation_Name"]=="Create-Thumbnail") & (df["resultCode"]== "201"), "duration"].values[0]
        t13 = (self.strptime_pro(t12, time_format) +  datetime.timedelta(milliseconds=t12_t13)).strftime(time_format)

        host_initialization = len(df.loc[(df["itemType"]=="trace") & (df["customDimensions"].str.contains("Host initialization"))])
        f1_cold_start = 0 if (host_initialization == 0) else 1
        f2_cold_start = 0 if (host_initialization == 0) else 1

    
        # print(f'id:{id}') 
        # print(f"t1: {t1}")
        # print(f"t2: {t2}")
        # print(f"t3: {t3}")
        # print(f"t4: {t4}")
        # print(f"t5: {t5}")
        # print(f"t6: {t6}")
        # print(f"t7: {t7}")
        # print(f"t8: {t8}")
        # print(f't9: {t9}')
        # print(f't10: {t10}')
        # print(f't11: {t11}')
        # print(f't12: {t12}')
        # print(f't13: {t13}')

        output = {
            'trace_id': id,
            't1': ft(t1),
            't2': ft(t2),
            't3': ft(t3),
            't4': ft(t4),
            't5': ft(t5),
            't6': ft(t6),
            't7': ft(t7),
            't8': ft(t8),
            't9': ft(t9),
            't10': ft(t10),
            't11': ft(t11),
            't12': ft(t12),
            't13': ft(t13),
            'f1_cold_start': f1_cold_start,
            'f2_cold_start': f2_cold_start
        }

        return output

