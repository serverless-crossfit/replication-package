"""Contant workload
Runs an experiment for the thumbnail_generator app with constant workload that keeps 
1 interaction per 10 seconds for 50 minutes
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
        "constant": {
            "executor": "constant-arrival-rate",
            "rate": 1,
            "timeUnit": "10s",
            "duration": "50m",
            "preAllocatedVUs": 20,
            "maxVUs": 50
        }
    }
}


def run_test(sb):

    try:
        # sb.prepare()
        sb.config.set('label', 'experiment_non_bursty_1.py')
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
