import os
import pandas as pd
from pathlib import Path

from time import time, sleep
import json
import subprocess
import warnings
import paho.mqtt.client as mqtt_client
from pprint import pformat
import threading

from ax.service.ax_client import AxClient

from pymongo.mongo_client import MongoClient

username_key = "HIVEMQ_USERNAME"
password_key = "HIVEMQ_PASSWORD"
host_key = "HIVEMQ_HOST"
course_id_key = "COURSE_ID"

sensor_data_fname = "results.json"
payload_dict_fname = "payload_dicts.json"
ax_client_fname = "ax_client_snapshot.json"

n_decimals = 4


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


def run_color_experiment(R, G, B):
    """Dummy function for receiving R, G, B values and returning sensor data."""
    wavelengths = [410, 440, 470, 510, 550, 583, 620, 670]
    rw = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.9, 1.0]
    gw = [0.2, 0.4, 0.6, 0.8, 1.0, 0.8, 0.4, 0.2]
    bw = [0.9, 1.0, 0.8, 0.6, 0.4, 0.2, 0.1, 0.0]
    sensor_data = {
        f"ch{wavelength}": rw[i] * R + gw[i] * G + bw[i] * B
        for i, wavelength in enumerate(wavelengths)
    }
    return sensor_data


def test_orchestrator_client():
    """Pretend to be the microcontroller"""

    # More of a check to the student than a test
    script_name = "orchestrator.py"
    script_content = open(script_name).read()

    if "..." in script_content:
        warnings.warn(
            f"Please complete the '...' sections in {script_name} and remove the '...' from each section"
        )

    course_id = os.getenv(course_id_key)
    assert (
        course_id is not None
    ), f"Please set the COURSE_ID environment variable per the README instructions."  # noqa: E501

    host = os.environ["HIVEMQ_HOST"]
    username = os.environ["HIVEMQ_USERNAME"]
    password = os.environ["HIVEMQ_PASSWORD"]
    course_id = os.environ["COURSE_ID"]

    command_topic = f"{course_id}/neopixel"
    sensor_data_topic = f"{course_id}/as7341"

    session_id_fname = "session_id.txt"
    csv_fname = "results.csv"

    # Remove files if they exist
    for filename in [
        sensor_data_fname,
        payload_dict_fname,
        ax_client_fname,
        session_id_fname,
        csv_fname,
    ]:
        file_path = Path(filename)
        file_path.unlink(missing_ok=True)

    connected_event = threading.Event()

    def on_connect(client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        client.subscribe(command_topic, qos=2)
        connected_event.set()

    # Create lists to store commands and sensor data
    received_payloads = []
    sent_payload_dicts = []

    def on_message(client, userdata, message):
        topic = message.topic
        msg = message.payload.decode()

        print(f"Received message on topic {topic}: {msg}")

        if topic == command_topic:
            print("Topic matches command_topic")
            received_payload_dict = json.loads(msg)
            received_payloads.append(
                received_payload_dict
            )  # Store the received command
            cmd = received_payload_dict["command"]
            sensor_data = run_color_experiment(cmd["R"], cmd["G"], cmd["B"])

            # Join params and sensor_data into the payload
            payload_dict = {**received_payload_dict, "sensor_data": sensor_data}
            payload = json.dumps(payload_dict)

            # slight delay to allow real microcontroller to go first if
            # it's running at the same time
            sleep(2.0)

            client.publish(sensor_data_topic, payload, qos=2)
            sent_payload_dicts.append(payload_dict)  # Store the sent sensor data
            # payload_dict_queue.put(payload_dict)  # Add sensor data to the queue

    client = mqtt_client.Client()
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_message = on_message

    client.tls_set(tls_version=mqtt_client.ssl.PROTOCOL_TLS_CLIENT)
    client.connect(host, port=8883)
    client.loop_start()

    # Wait for the client to connect
    connected_event.wait(timeout=10.0)

    def run_subprocess(script_name):
        orchestrator_client_process = subprocess.Popen(
            ["python", script_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )

        # Wait for the subprocess to finish and get its output
        stdout, stderr = orchestrator_client_process.communicate(timeout=300)

        # Check the exit code
        if orchestrator_client_process.returncode != 0:
            print(
                f"Subprocess exited with code {orchestrator_client_process.returncode}"
            )
            print(f"Stdout: {stdout}")
            print(f"Stderr: {stderr}")

    thread = threading.Thread(target=run_subprocess, args=(script_name,))
    thread.daemon = True  # Ensure the thread is killed after main thread finishes
    thread.start()  # without threading, it would hang after 9 commands

    try:
        # give the data some time to be sent
        start_time = time()
        timeout = 420  # seconds
        lower_limit = 15  # seconds, to ensure success even when microcontroller is running concurrently

        n = 0
        while (
            not os.path.exists(ax_client_fname)
            and not os.path.exists(payload_dict_fname)
            and not os.path.exists(sensor_data_fname)
        ) or time() - start_time < lower_limit:
            if len(received_payloads) > n:
                print(f"Received {len(received_payloads)} commands.")
                n = len(received_payloads)
            if time() - start_time > timeout:
                raise TimeoutError(
                    f"{sensor_data_fname} and/or {payload_dict_fname} and/or {ax_client_fname} not found within {timeout} s. Number of commands received so far: {len(received_payloads)}"  # noqa: E501
                )

        client.loop_stop()

        sleep(30)

        def to_sorted_rounded_frozenset_list(dict_list):
            rounded_dict_list = []
            for d in dict_list:
                rounded_dict = {
                    k: round(v, 5) if isinstance(v, float) else v for k, v in d.items()
                }
                rounded_dict_list.append(rounded_dict)
            return sorted(frozenset(d.items()) for d in rounded_dict_list)

        # Check that the experiment_id key is present in all received commands and unique
        assert all(
            "experiment_id" in command for command in received_payloads
        ), f"Received commands {received_payloads} do not contain experiment_id key"  # noqa: E501
        assert len(
            set(command["experiment_id"] for command in received_payloads)
        ) == len(
            received_payloads
        ), f"Received commands {received_payloads} do not have unique experiment_id keys"  # noqa: E501

        ax_client = AxClient.load_from_json_file(ax_client_fname)

        # # assert that random_seed is set to 42 # REVIEW: Is this necessary? #NOTE: the JSON method doesn't retain _random_seed, see Ax issue
        # assert (
        #     ax_client._random_seed == 42
        # ), f"Expected {AxClient.__name__} object to have random_seed=42, got {ax_client._random_seed}"  # noqa: E501

        # extract all data from the AxClient object
        ax_client_data_df = ax_client.get_trials_data_frame()[["mae", "R", "G", "B"]]
        ax_client_data = ax_client_data_df.to_dict(orient="records")

        with open(sensor_data_fname) as f:
            results_dicts = json.load(f)

        # TODO: Check that ax_client_data (RGB, mae) and results_dicts (RGB, mae) match
        # Ensure both lists have the same length
        assert len(ax_client_data) == len(
            results_dicts
        ), "ax_client_data and results_dicts have different lengths"

        # Compare the values for the R, G, B, and mae keys in each dictionary
        for i, (ax_data, results_data) in enumerate(zip(ax_client_data, results_dicts)):
            for key in ["R", "G", "B", "mae"]:
                if key == "mae":
                    results_value = round(results_data["mae"], 4)
                else:
                    results_value = results_data["command"][key]
                assert (
                    ax_data[key] == results_value
                ), f"ax_client_data and results_dicts do not match at index {i} for key {key}. ax_client_data: {ax_data}, results_dicts: {results_data}"

        with open(payload_dict_fname) as f:
            payload_dicts_for_microcontroller = json.load(f)

        target_command = {"R": 38, "G": 79, "B": 63}  # HACK: Hardcoded

        orchestrator_rgb_values = [
            {k: v for k, v in payload_dict["command"].items() if k in ("R", "G", "B")}
            for payload_dict in sent_payload_dicts
        ]

        # drop target_command from orchestrator_rgb_values
        orchestrator_rgb_values = [
            d for d in orchestrator_rgb_values if d != target_command
        ]

        microcontroller_rgb_values = [
            {k: v for k, v in payload_dict["command"].items() if k in ("R", "G", "B")}
            for payload_dict in payload_dicts_for_microcontroller
        ]

        received_rgb_values = [
            {k: v for k, v in payload_dict["command"].items() if k in ("R", "G", "B")}
            for payload_dict in received_payloads
        ]

        # drop target_command from received_rgb_values
        received_rgb_values = [d for d in received_rgb_values if d != target_command]

        # Check that rgb_values and sent_rgb_values match, regardless of order
        # TODO: also check received payloads with another == (does this work?)
        assert (
            to_sorted_rounded_frozenset_list(orchestrator_rgb_values)
            == to_sorted_rounded_frozenset_list(microcontroller_rgb_values)
            == to_sorted_rounded_frozenset_list(received_rgb_values)
        ), f"Mismatch between microcontroller RGB commands, orchestrator.py RGB commands, and received RGB commands. Microcontroller:\n{microcontroller_rgb_values}\n\nOrchestrator:\n{orchestrator_rgb_values}\n\nReceived:\n{received_rgb_values}"  # noqa: E501

        # TODO: Check that entries pulled directly from MongoDB match results.csv (?)

        database_name = os.environ["DATABASE_NAME"]
        collection_name = os.environ["COLLECTION_NAME"]
        connection_string = os.environ["CONNECTION_STRING"]

        db_client = MongoClient(connection_string)

        # Send a ping to confirm a successful connection
        try:
            db_client.admin.command("ping")
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print(e)

        db = db_client[database_name]
        collection = db[collection_name]

        with open(session_id_fname) as f:
            session_id = f.read().strip()

        # get all results that have the same session ID as this run
        results = list(collection.find({"session_id": session_id}))

        assert (
            len(results) > 0
        ), f"No MongoDB results found for session ID: {session_id}. Ensure the microcontroller is actively running experiments and has logged them to MongoDB with the correct session ID"

        # Create pandas DataFrame from database
        df = pd.json_normalize(results).set_index("_id").round(n_decimals)

        check_df = pd.read_csv(csv_fname).set_index("_id").round(n_decimals)

        # Select only the columns of df that are present in check_df, round, and drop duplicates
        df_selected = df[check_df.columns].round(n_decimals).drop_duplicates()

        # Merge check_df with df_selected on common columns
        merged_df = pd.merge(check_df, df_selected, how="left", indicator=True)

        # Check that all rows in check_df have a match in df_selected
        df_matches = merged_df["_merge"] == "both"
        assert df_matches.all(), (
            "Not all entries in the expected data have a match in the actual data.\n"
            f"Expected DataFrame:\n{check_df.to_string()}\n"
            f"Actual DataFrame:\n{df_selected.to_string()}\n"
            f"Matches:\n{df_matches}"
        )

        assert (
            len(results) == 21
        ), f"Expected 21 results (1 target, 20 iterations), got {len(results)}"

    except Exception as e:
        blinded_credentials = {
            username_key: (
                username
                if len(username) < 4
                else username[:2] + "*" * (len(username) - 4) + username[-2:]
            ),
            password_key: "*" * len(password),
            host_key: (
                host if len(host) < 4 else host[:2] + "*" * (len(host) - 4) + host[-2:]
            ),
            course_id_key: course_id,
            "command_topic": command_topic,
            "sensor_data_topic": sensor_data_topic,
        }
        raise Exception(
            f"{e}. Please check {script_name} and refer back to the README. For reference, the following (blinded) credentials were used during this run: \n{pformat(blinded_credentials)}\n"  # noqa: E501
        ) from e
    finally:
        # Stop the orchestrator_client.py process

        print(f"Reading STDOUT and STDERR from {script_name} process")


if __name__ == "__main__":
    test_orchestrator_client()
