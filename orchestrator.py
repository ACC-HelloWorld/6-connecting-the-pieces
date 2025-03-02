# Description: Send commands to HiveMQ and receive sensor data from HiveMQ

# NOTE: for this to work properly, you are expected to be running the
# microcontroller.py script on your Pico W
import os
import json
import secrets
import threading
from time import time

import numpy as np
import pandas as pd

from queue import Queue, Empty
import paho.mqtt.client as paho

from ax.service.ax_client import AxClient, ObjectiveProperties
import plotly.graph_objects as go
from sklearn.metrics import mean_absolute_error

from pymongo.mongo_client import MongoClient

course_id = os.environ["COURSE_ID"]

username = os.environ["HIVEMQ_USERNAME"]
password = os.environ["HIVEMQ_PASSWORD"]
host = os.environ["HIVEMQ_HOST"]

database_name = os.environ["DATABASE_NAME"]
collection_name = os.environ["COLLECTION_NAME"]
atlas_uri = os.environ["ATLAS_URI"]

# Topics
neopixel_topic = f"{course_id}/neopixel"
as7341_topic = f"{course_id}/as7341"

# create random session id to keep track of the session and filter out old data
session_id = ...  # IMPLEMENT

with open("session_id.txt", "w") as f:  
    f.write(session_id)  

num_iter = 20
target_command = {"R": 38, "G": 79, "B": 63}

# %% MQTT Communication


def get_client_and_queue(
    subscribe_topic, host, username, password=None, port=8883, tls=True
):
    """
    This function creates a new Paho MQTT client, connects it to the specified
    host, and subscribes it to the specified topic. It also creates a queue for
    storing incoming messages and sets up event handlers for handling connection
    and message events.

    Parameters
    ----------
    subscribe_topic : str
        The MQTT topic that the client should subscribe to.
    host : str
        The hostname or IP address of the MQTT server to connect to.
    username : str
        The username to use for MQTT authentication.
    password : str, optional
        The password to use for MQTT authentication, by default None.
    port : int, optional
        The port number to connect to at the MQTT server, by default 8883.
    tls : bool, optional
        Whether to use TLS for the connection, by default True.

    Returns
    -------
    tuple
        A tuple containing the Paho MQTT client and the queue for storing
        incoming messages.

    Examples
    --------
    >>> client, queue = get_client_and_queue("test/topic", "mqtt.example.com", "username", "password")
    """
    client = paho.Client()  # create new instance
    queue = Queue()  # Create queue to store sensor data
    connected_event = threading.Event()  # event to wait for connection

    def on_message(client, userdata, msg):
        print(f"Received message on topic {msg.topic}: {msg.payload}")
        # TODO: Convert msg (a JSON string) into a dictionary
        # TODO: Put the dictionary into the queue
        ...

    def on_connect(client, userdata, flags, rc):
        client.subscribe(subscribe_topic, qos=2)
        connected_event.set()

    client.on_connect = on_connect
    client.on_message = on_message

    # enable TLS for secure connection
    if tls:
        client.tls_set(tls_version=paho.ssl.PROTOCOL_TLS_CLIENT)  # type: ignore

    # set username and password
    client.username_pw_set(username, password)

    # connect to HiveMQ Cloud on port 8883 (default for MQTT)
    client.connect(host, port)

    client.subscribe(subscribe_topic, qos=2)
    # wait for connection to be established

    connected_event.wait(timeout=10.0)
    return client, queue


# Function to send a command to the neopixel and wait for sensor data
def run_experiment(
    client, queue, command_topic, payload_dict, queue_timeout=30, function_timeout=300
):
    """
    This function sends a command to the neopixel, waits for sensor data, and
    returns the results.

    Parameters
    ----------
    client : paho.mqtt.client.Client
        The Paho MQTT client to use for sending the command and receiving the
        results.
    queue : queue.Queue
        The queue where incoming messages from the MQTT client will be stored.
    command_topic : str
        The MQTT topic to publish the command to.
    payload_dict : dict
        The dictionary containing the command and experiment_id. The command
        should be a dictionary with 'R', 'G', and 'B' keys.
    queue_timeout : int, optional
        The number of seconds to wait for a message in the queue before timing
        out, by default 30.
    function_timeout : int, optional
        The number of seconds to wait for the function to complete before timing
        out, by default 300.

    Returns
    -------
    dict
        The results of the experiment, as a dictionary.

    Raises
    ------
    TimeoutError
        If the function does not complete within the specified function_timeout.
    queue.Empty
        If no message is received in the queue within the specified
        queue_timeout.

    Examples
    --------
    >>> run_experiment(client, queue, "test/topic", {"command": {"R": 255, "G": 255, "B": 255}, "experiment_id": 1})
    {"experiment_id": 1, "sensor_data": {<sensor_data>}, "command": {"R": 255, "G": 255, "B": 255}}
    """
    # TODO: Convert payload_dict into a JSON string
    # TODO: Publish the JSON string to the command_topic with qos=2
    ...  # IMPLEMENT

    client.loop_start()

    t0 = time()
    while True:
        if time() - t0 > function_timeout:
            raise TimeoutError(
                f"Function timed out without valid data ({function_timeout} seconds)"
            )
        try:
            results = queue.get(True, timeout=queue_timeout)
        except Empty as e:
            raise Empty(
                f"Sensor data retrieval timed out ({queue_timeout} seconds)"
            ) from e

        # only return the data if it matches the expected experiment id
        if (
            isinstance(results, dict)
            and results["experiment_id"] == payload_dict["experiment_id"]
        ):
            client.loop_stop()
            return results


# Orchestrator subscribes to the sensor data topic
mqtt_client, queue = get_client_and_queue(
    as7341_topic, host, username, password=password
)

# %% Bayesian Optimization

target_payload_dict = {
    "command": target_command,
    "experiment_id": "target",
    "session_id": session_id,
}

target_results = run_experiment(mqtt_client, queue, neopixel_topic, target_payload_dict)
print(f"Target results: {target_results}")
target_sensor_data = target_results["sensor_data"]

payload_dicts = []  # For autograding
results_dicts = []  # For autograding

obj_name = "mae"


def evaluate(command):
    """
    This function sends a command to the neopixel, waits for sensor data,
    calculates the mean absolute error (MAE) between the received sensor data
    and target sensor data, and returns a dictionary with the object name and
    MAE.

    Parameters
    ----------
    command : dict
        The command to be sent to the neopixel. This should be a dictionary with
        'R', 'G', and 'B' keys.

    Returns
    -------
    dict
        A dictionary with the object name as the key and the calculated MAE as
        the value.

    Examples
    --------
    >>> evaluate({"R": 255, "G": 255, "B": 255})
    {"mae": 12.34}
    """
    # create a random experiment id to keep track where the sensor data is from
    experiment_id = ...  # IMPLEMENT

    # create a payload dictionary with the command, experiment id, and session id
    payload_dict = {
        "command": command,
        "experiment_id": experiment_id,
        "session_id": session_id,
    }

    results_dict = run_experiment(mqtt_client, queue, neopixel_topic, payload_dict)

    # calculate MAE between sensor data and target sensor data
    mae = ...  # IMPLEMENT

    payload_dicts.append(payload_dict)  # For autograding
    results_dict["mae"] = mae  # for autograding
    results_dicts.append(results_dict)  # for autograding

    return ...  # IMPLEMENT


# Define the parameters per the README.md file instructions
parameters = ...  # IMPLEMENT

# define the objective with the name "mae" (mean absolute error) and minimize=True
objectives = ...  # IMPLEMENT

# Instantiate the AxClient class with a random seed for reproducibility
ax_client = AxClient(random_seed=42)

# Use the create_experiment method from the AxClient class to pass the
# parameters and objective(s)
ax_client.create_experiment(parameters=parameters, objectives=objectives)

for _ in range(num_iter):
    parameterization, trial_index = ax_client.get_next_trial()
    # e.g., parameterization={"R": 10, "G": 20, "B": 15} and trial_index=0
    results = evaluate(parameterization)
    ax_client.complete_trial(trial_index=trial_index, raw_data=results)


best_parameters, metrics = ax_client.get_best_parameters()

# Extract the values in the order of the keys in target_command
target_rgb_values = list(target_command.values())
best_predicted_rgb_values = [best_parameters[key] for key in target_command.keys()]

# Calculate the mean absolute error
true_mismatch = mean_absolute_error(target_rgb_values, best_predicted_rgb_values)

print(f"Target color: {target_command}")
print(f"Best observed color: {best_parameters}")
print(f"Color misfit: {np.round(true_mismatch, 1)}")

# Save the entire Ax experiment to a JSON file
...  # IMPLEMENT

# get the AxClient's optimization trace using the built-in plotting method (objective_optimum can be left off)
optimization_trace = ...  # IMPLEMENT


def to_plotly(axplotconfig):
    """Converts AxPlotConfig to plotly Figure."""
    data = axplotconfig[0]["data"]
    layout = axplotconfig[0]["layout"]
    fig = go.Figure({"data": data, "layout": layout})
    return fig


# Convert the optimization trace to a Plotly figure and save it as an image
fig = to_plotly(optimization_trace)
image_name = "optimization_trace.png"
fig.write_image(image_name)

# Open the image file in Codespaces (or Visual Studio Code)
os.system(f"code {image_name}")

# write the commands with experiment ids to a file (for autograding)
with open("payload_dicts.json", "w") as f:
    json.dump(payload_dicts, f)

# write the sensor data to a file (for autograding)
with open("results.json", "w") as f:
    json.dump(results_dicts, f)

# %% Data logging

# TODO: Create MongoDB client using connection string
# Hint: Use MongoClient(connection_string)
client = ...

# TODO: Get database and collection objects
# Hint: Use client[database_name] and db[collection_name]
db = ...
collection = ...

# TODO: Query documents with matching session_id
# Hint: Use collection.find({"session_id": session_id})
results = ...

# TODO: Create pandas DataFrame from results
# Hint: Use pd.json_normalize()
df = ...

# TODO: Export DataFrame to CSV file
# Hint: Use df.to_csv()
...

# TODO: Close MongoDB client
# Hint: Use client.close()
...
