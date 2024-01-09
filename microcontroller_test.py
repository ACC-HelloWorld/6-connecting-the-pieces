import os

from credentials_test import course_id_key

import json
from communication import hivemq_communication
import secrets
from queue import Empty
import warnings

from neopixel import NeoPixel

import ast
from as7341_sensor import Sensor


def test_read_script():
    script_content = open("microcontroller.py").read()
    tree = ast.parse(script_content)

    class SensorVariableVisitor(ast.NodeVisitor):
        def __init__(self):
            self.sensor_vars = []

        def visit_Assign(self, node):
            if (
                isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == Sensor.__name__
            ):
                self.sensor_vars.extend(target.id for target in node.targets)

    visitor = SensorVariableVisitor()
    visitor.visit(tree)

    assert len(visitor.sensor_vars) > 0, "No variables of Sensor class found"


def test_blink_script():
    script_content = open("microcontroller.py").read()
    tree = ast.parse(script_content)

    class NeoPixelVariableVisitor(ast.NodeVisitor):
        def __init__(self):
            self.neopixel_vars = []

        def visit_Assign(self, node):
            if (
                isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == NeoPixel.__name__
            ):
                self.neopixel_vars.extend(target.id for target in node.targets)

    visitor = NeoPixelVariableVisitor()
    visitor.visit(tree)

    assert len(visitor.neopixel_vars) > 0, "No variables of NeoPixel class found"


def flatten_dict(d, parent_key="", sep="_"):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    flattened = dict(items)
    if len(items) != len(set(k for k, v in items)):
        raise ValueError("Overlapping keys encountered.")
    return flattened


def test_send_and_receive():
    """act as the orchestrator"""

    # More of a check to the student than a test
    script_name = "microcontroller.py"
    script_content = open(script_name).read()

    if "..." in script_content:
        warnings.warn(
            f"Please complete the '...' sections in {script_name} and remove the '...' from each section"
        )

    COURSE_ID = os.environ[course_id_key]

    command = {"R": 48, "G": 213, "B": 200}  # turquoise :)

    publish_topic = f"{COURSE_ID}/neopixel"
    subscribe_topic = f"{COURSE_ID}/as7341"

    # Generate a random string of 8 characters (4 bytes)
    payload_dict = {"command": command, "experiment_id": secrets.token_hex(4)}
    payload = json.dumps(payload_dict)
    try:
        payload_data = hivemq_communication(payload, subscribe_topic, publish_topic)
        print(f"Received payload: {payload_data}")
    except (Empty, TimeoutError) as e:
        raise Empty(
            f"Did not receive any data on topic {subscribe_topic} after publishing to {publish_topic}. Refer to troubleshooting checklist in the README."  # noqa: E501
        ) from e

    payload_data_check = {
        **payload_dict,
        "sensor_data": {
            "ch410": 0,
            "ch440": 0,
            "ch470": 0,
            "ch510": 0,
            "ch550": 0,
            "ch583": 0,
            "ch620": 0,
            "ch670": 0,
        },
    }

    flat_check = flatten_dict(payload_data_check)
    flat_data = flatten_dict(payload_data)

    # Check that at minimum the keys in the check are in the data
    assert set(flat_check.keys()).issubset(
        set(flat_data.keys())
    ), f"sensor_data_check: {payload_data_check} is not a subset of sensor_data: {payload_data}"  # noqa: E501

    experiment_id_data = payload_data["experiment_id"]
    experiment_id_check = payload_data_check["experiment_id"]

    assert (
        experiment_id_data == experiment_id_check
    ), f"experiment_id: {experiment_id_data} != {experiment_id_check}"


if __name__ == "__main__":
    test_read_script()
    test_blink_script()
    test_send_and_receive()
