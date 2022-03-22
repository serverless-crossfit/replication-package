# Experiment Plans

The following experiment plans automate benchmarking experiments with different types workloads (constant and bursty).

## Replicate Cloud Experiment

1. Deploy the thumbnail generator application as described in the [README](../thumbnail-generator/README.md).
2. Run the experiment plan via `python experiment_bursty_1.py` to automate invocation, trace retrieval, and trace analysis. The workloads used in the paper are:
    * `experiment_bursty_1.py`
    * `experiment_bursty_2.py`
    * `experiment_bursty_3.py`
    * `experiment_constant_3.py`
