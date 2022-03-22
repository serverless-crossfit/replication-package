"""Bursty workload
Runs an experiment for the thumbnail_generator app with bursty workload
- non-bursty stage: RPS 1
- bursty stage: RPS 50
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
        "burst_stage_1": {
            "executor": "constant-arrival-rate",
            "rate": 1,
            "timeUnit": "1s",
            "duration": "10s",
            "preAllocatedVUs": 10,
            "maxVUs": 10
        },
        "burst_stage_2": {
            "executor": "constant-arrival-rate",
            "rate": 50,
            "timeUnit": "1s",
            "duration": "5s",
            "preAllocatedVUs": 50,
            "maxVUs": 100,
            "startTime": "10s"
        },
        "burst_stage_3": {
            "executor": "constant-arrival-rate",
            "rate": 1,
            "timeUnit": "1s",
            "duration": "40s",
            "preAllocatedVUs": 10,
            "maxVUs": 10,
            "startTime": "15s"
        }
    }
}


def run_test(sb):

    try:
        # sb.prepare()
        sb.config.set('label', 'experiment_bursty_3.py')
        sb.invoke('custom', workload_options=options)
        sb.wait(5 * 60)
        sb.get_traces()
        sb.analyze_traces()
    except:
        logging.error('Error during execution of benchmark. Cleaning up ...')
    # finally:
    #     sb.cleanup()

# for i in range(1):
for sb in sb_clis:
    run_test(sb)
