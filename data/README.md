# Data

The `AWS` and `Azure` sub-directories contain data from benchmark executions from January 2022.

Each execution is a separate directory with a timestamp in the format `yyyy-mm-dd-HH-MM-SS` (e.g., `2022-01-06_10-38-44`) and contains the following files:

* `k6_metrics.csv`: Load generator HTTP client logs in CSV format (see [K6 docs](https://k6.io/docs/results-visualization/csv/))
* `sb_config.yml`: serverless benchmarker execution configuration including experiment label.
* `trace_breakdown.csv`: analyzer output CSV per trace. Contains the `trace_id`, all timestamps (`t1`-`t13`), and coldstart flags (`f1_cold_start=1|0`).
* `trace_ids.txt`: text file with each trace id on a new line.
* `traces.json`: raw trace JSON representation as retrieved from the provider tracing service. For AWS, see [X-Ray segment docs](https://docs.aws.amazon.com/xray/latest/devguide/xray-api-segmentdocuments.html). For Azure, see [Application Insights telemetry data model](https://docs.microsoft.com/en-us/azure/azure-monitor/app/data-model).
* `workload_options.json`: [K6 load scenario](https://k6.io/docs/using-k6/scenarios/) configuration.

## Execution Mappings

Summary of workload to execution mappings.
These are dynamically derived based on the benchmark metadata during data import.

```python
aws_executions = {
    'bursty_1': 'AWS/2022-01-06_13-38-16',
    'bursty_2': 'AWS/2022-01-06_17-02-45',
    'bursty_3': 'AWS/2022-01-06_18-53-29',
    'constant_1': 'AWS/2022-01-06_23-53-09',
    'constant_2': 'AWS/2022-01-06_12-00-34',
    'constant_3': 'AWS/2022-01-06_10-38-44',
}
azure_executions = {
    'bursty_1': 'Azure/2022-01-06_13-44-53',
    'bursty_2': 'Azure/2022-01-06_17-09-03',
    'bursty_3': 'Azure/2022-01-06_18-59-42',
    'constant_1': 'Azure/2022-01-07_00-48-24',
    'constant_2': 'Azure/2022-01-06_12-30-50',
    'constant_3': 'Azure/2022-01-06_10-49-01',
}
```
