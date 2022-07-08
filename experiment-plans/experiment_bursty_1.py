"""Bursty workload
Runs an experiment for the thumbnail_generator app with bursty workload
- non-bursty stage: RPS 1
- bursty stage: RPS 12
- Target requests: 300
"""

import logging
from pathlib import Path
from sb.sb import Sb

apps_dir = Path('../thumbnail-generator')
apps = [
    'AWS/thumbnail_benchmark.py',
    'Azure/thumbnail_benchmark.py'
]
app_paths = [(apps_dir / a).resolve() for a in apps]

sb_clis = [Sb(p, log_level='DEBUG', debug=True) for p in app_paths]

options = {
    "scenarios": {
        "stage_1": {
            "executor": "constant-arrival-rate",
            "rate": 1,
            "timeUnit": "1s",
            "duration": "10s",
            "preAllocatedVUs": 10,
            "maxVUs": 10
        },
        "stage_2": {
            "executor": "constant-arrival-rate",
            "rate": 12,
            "timeUnit": "1s",
            "duration": "5s",
            "preAllocatedVUs": 50,
            "maxVUs": 100,
            "startTime": "10s"
        },
        "stage_3": {
            "executor": "constant-arrival-rate",
            "rate": 1,
            "timeUnit": "1s",
            "duration": "10s",
            "preAllocatedVUs": 10,
            "maxVUs": 10,
            "startTime": "15s"
        },
        "stage_4": {
            "executor": "constant-arrival-rate",
            "rate": 12,
            "timeUnit": "1s",
            "duration": "5s",
            "preAllocatedVUs": 50,
            "maxVUs": 100,
            "startTime": "25s"
        },
        "stage_5": {
            "executor": "constant-arrival-rate",
            "rate": 1,
            "timeUnit": "1s",
            "duration": "10s",
            "preAllocatedVUs": 10,
            "maxVUs": 10,
            "startTime": "30s"
        },
        "stage_6": {
            "executor": "constant-arrival-rate",
            "rate": 12,
            "timeUnit": "1s",
            "duration": "5s",
            "preAllocatedVUs": 10,
            "maxVUs": 10,
            "startTime": "40s"
        },
        "stage_7": {
            "executor": "constant-arrival-rate",
            "rate": 1,
            "timeUnit": "1s",
            "duration": "10s",
            "preAllocatedVUs": 10,
            "maxVUs": 10,
            "startTime": "45s"
        },
        "stage_8": {
            "executor": "constant-arrival-rate",
            "rate": 12,
            "timeUnit": "1s",
            "duration": "5s",
            "preAllocatedVUs": 10,
            "maxVUs": 10,
            "startTime": "55s"
        },
        "stage_9": {
            "executor": "constant-arrival-rate",
            "rate": 1,
            "timeUnit": "1s",
            "duration": "20s",
            "preAllocatedVUs": 10,
            "maxVUs": 10,
            "startTime": "60s"
        }
    }
}


def run_test(sb):

    try:
        sb.prepare()
        sb.config.set('label', 'experiment_bursty_1.py')
        sb.invoke('custom', workload_options=options)
        sb.wait(5 * 60)
        sb.get_traces()
        sb.analyze_traces()
    except:
        logging.error('Error during execution of benchmark. Cleaning up ...')
    finally:
        sb.cleanup()

# for i in range(1):
for sb in sb_clis:
    run_test(sb)
