import json
from sb.workload_generator import WorkloadGenerator


def test_default_workload():
    actual = json_options('single')
    assert actual == '{"vus": 1, "iterations": 1}'


def test_invoke_numeric_workload():
    actual = json_options(10)
    assert actual == '{"vus": 1, "iterations": 10}'


def test_jump_workload():
    actual = json_options('jump')
    expected_start = '''{"scenarios": {"benchmark_scenario": {"executor": "ramping-arrival-rate", "startRate": 0, "timeUnit": "1s", "preAllocatedVUs": 1, "stages": [{"target": 0, "duration": "8s"}, {"target": 1, "duration": "1s"}, {"target": 1, "duration": "1s"}, {"target": 0, "duration": "1s"}, {"target": 0, "duration": "2s"}'''  # noqa: E501
    assert actual.startswith(expected_start)


# Helper returning a JSON-string based on given args for the workload generator
def json_options(*args):
    generator = WorkloadGenerator(*args)
    workload_dict = generator.generate_trace()
    return json.dumps(workload_dict)
