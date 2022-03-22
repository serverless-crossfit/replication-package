"""
Generates all plots by loading and analyzing all executions
"""

# %% Imports
from data_importer import *
import seaborn as sns
import matplotlib.pyplot as plt


# %% Load data
execution_paths = find_execution_paths(data_path)
trace_breakdown_dfs = []
for execution in execution_paths:
    app_config, app_name = read_sb_app_config(execution)
    trace_breakdown = read_trace_breakdown(execution)
    trace_breakdown['provider'] = app_config.get('provider', None)
    trace_breakdown['label'] = app_config.get('label', None)
    trace_breakdown_dfs.append(trace_breakdown)

# Combine data frames
traces = pd.concat(trace_breakdown_dfs)

# %% Preprocess data
warm_traces = filter_traces_warm(traces)
durations = calculate_durations(warm_traces)
durations_long = pd.melt(durations, id_vars=['trace_id', 'provider', 'label'], var_name='duration_type', value_vars=timedelta_cols, value_name='duration')
durations_long['duration_ms'] = durations_long['duration'].dt.total_seconds() * 1000

# Rename and reorder categories
durations_long['workload_type'] = durations_long['label'].map(label_mappings)
durations_long['workload_type'] = pd.Categorical(durations_long['workload_type'],
                                                 categories=label_mappings.values(),
                                                 ordered=True)
durations_long['provider'] = durations_long['provider'].map(provider_mappings)
durations_long['provider'] = pd.Categorical(durations_long['provider'],
                                            categories=provider_mappings.values(),
                                            ordered=True)
durations_long['duration_type'] = durations_long['duration_type'].map(duration_mappings)
durations_long['duration_type'] = pd.Categorical(durations_long['duration_type'],
                                            categories=duration_mappings.values(),
                                            ordered=True)

# Remove negative timediffs
# NOTE: discovered 1 exceptional case in AWS/2022-01-06_12-00-34
# The trace with the id 1-61d6cc48-311d13027290fcb942b23928 has
# a negative duration of -115.229 ms between t6t7 (trigger time)
durations_long = durations_long.drop(durations_long[durations_long['duration_ms']<0].index)

# Clip data because catplot doesn't support dynamic limits
# and the tail is too long to be shown.
# Important: This needs to be described when presenting
# Based on StackOverflow: https://stackoverflow.com/a/54356494
def is_outlier(s):
    lower_limit = s.min()
    # upper_limit = s.quantile(.95)
    upper_limit = s.median() + 3 * s.std()
    return ~s.between(lower_limit, upper_limit)

# durations_long_filtered = durations_long.loc[~durations_long.groupby(['provider', 'workload_type', 'duration_type'])['duration_ms'].apply(is_outlier), :].reset_index(drop=True)
durations_long_filtered = durations_long

# %% Summary stats table
stats = durations_long.groupby(['workload_type', 'duration_type', 'provider'])['duration_ms'].agg(
    min='min',
    mean='mean',
    p50=(lambda x: x.quantile(0.5)),
    p95=(lambda x: x.quantile(0.95)),
    p99=(lambda x: x.quantile(0.99)),
    max='max',
    std='std'
).reset_index()
stats.insert(3, 'median_std', stats['p50'].round(0).astype(str) + '±' + stats['std'].round(1).astype(str))
# stats['median_std'] = stats['p50'].astype(str) + '±' + stats['std'].round(1).astype(str)
stats.to_csv(f'{plots_path}/summary_stats.csv')

# %% Latency breakdown plot
# Filter
constant3 = durations_long_filtered[durations_long_filtered['workload_type']=='C3']
# Latency clusters based on duration range
small = ['CompF1', 'AuthF1', 'AuthF2r', 'AuthF2w']
medium = ['TrigH', 'InitF1', 'WriteF1', 'InitF2', 'ReadF2', 'CompF2', 'WriteF2']
large = ['TrigS', 'Total']
# Filter latency clusters
df_small = constant3[constant3['duration_type'].isin(small)].copy()
df_small['duration_type'] = df_small['duration_type'].cat.remove_unused_categories()
df_medium = constant3[constant3['duration_type'].isin(medium)].copy()
df_medium['duration_type'] = df_medium['duration_type'].cat.remove_unused_categories()
df_large = constant3[constant3['duration_type'].isin(large)].copy()
df_large['duration_type'] = df_large['duration_type'].cat.remove_unused_categories()

# Seaborn violin plot docs: https://seaborn.pydata.org/generated/seaborn.violinplot.html
# Initially from inverted color palette sns.color_palette('pastel')
# Adjusted for readability in grey-scale using https://coolors.co/000000-ffa639-cbe2fc
provider_color_mapping = {"AWS": "#FFA639", "Azure": "#CBE2FC"}
fig, (ax1, ax2, ax3) = plt.subplots(figsize=(10, 4), ncols=3, gridspec_kw={'width_ratios': [2, 7, 4]}, sharex=False, sharey=False)
# Large (left)
violin1 = sns.violinplot(data=df_large, x='duration_type', y='duration_ms', hue='provider', split=True,
    scale="count", palette=provider_color_mapping, cut=0, inner='quartile', ax=ax1, order=['Total', 'TrigS'])
violin1.set_xlabel("")
violin1.set_ylabel("Duration (ms)")
labels = violin1.get_xticklabels()
labels[0].set_fontweight('bold')
violin1.set_xticklabels(labels)
ax1.get_legend().remove()
ax1.tick_params(axis='x', labelrotation=90)
ax1.set_title('<2500 ms')
# Medium (middle)
violin2 = sns.violinplot(data=df_medium, x='duration_type', y='duration_ms', hue='provider', split=True,
    scale="count", palette=provider_color_mapping, cut=0, inner='quartile', ax=ax2, order=['TrigH', 'InitF1', 'InitF2', 'CompF2', 'WriteF1', 'ReadF2', 'WriteF2'])
violin2.set_xlabel("Operation")
violin2.set_ylabel("")
ax2.legend(title='Provider')
ax2.tick_params(axis='x', labelrotation=90)
ax2.set_title('<700 ms')
# Small (right)
violin3 = sns.violinplot(data=df_small, x='duration_type', y='duration_ms', hue='provider', split=True,
    scale="count", palette=provider_color_mapping, cut=0, inner='quartile', ax=ax3)
violin3.set_xlabel("")
violin3.set_ylabel("")
ax3.get_legend().remove()
ax3.tick_params(axis='x', labelrotation=90)
ax3.set_title('<70 ms')
plt.savefig(f'{plots_path}/latency_breakdown_constant3.pdf', bbox_inches='tight')
plt.clf()


# %% Workload type plot
# Filter
workload_types = ['C3', 'B1', 'B2', 'B3']
workload_type_labels = ['C', 'B1', 'B2', 'B3']
df_wl = durations_long_filtered[durations_long_filtered['workload_type'].isin(workload_types)].copy()
df_wl['workload_type'] = df_wl['workload_type'].cat.remove_unused_categories()
duration_types = ['Total', 'CompF2', 'WriteF1', 'InitF1']
df_wl = df_wl[df_wl['duration_type'].isin(duration_types)]
df_wl['duration_type'] = df_wl['duration_type'].cat.remove_unused_categories()

# Seaborn catplot docs: https://seaborn.pydata.org/generated/seaborn.catplot.html#seaborn.catplot
# FacetGrid for customizations: https://seaborn.pydata.org/generated/seaborn.FacetGrid.html
g = sns.catplot(x="workload_type", y="duration_ms",
                hue="provider", col="duration_type",
                data=df_wl,
                orient="v", height=2.4, aspect=1.1, palette=provider_color_mapping,
                kind="violin", split=True, inner="quart", cut=0, bw='scott', sharey=False, col_wrap=4,
                col_order=duration_types)
g.set_axis_labels("Workload type", "Duration (ms)")
g.set_xticklabels(workload_type_labels)
# Optionally customize the facet label title
g.set_titles("{col_name}")
# sns.move_legend(g, "upper center", bbox_to_anchor=(.5, 1.1), ncol=2, frameon=False, title='Provider') # title='Provider' | None
g._legend.set_title('Provider')
axes = g.axes.flatten()
axes[0].set_title("Total", fontweight='bold')
plt.savefig(f'{plots_path}/workload_types.pdf', bbox_inches='tight')
plt.clf()

# %%
