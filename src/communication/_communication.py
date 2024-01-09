import os
from paho.mqtt import client as mqtt_client
import threading

import json

# HACK: hardcoded (instead of using credentials_test.py)
username_key = "HIVEMQ_USERNAME"  # HACK: hardcoded
password_key = "HIVEMQ_PASSWORD"  # HACK: hardcoded
host_key = "HIVEMQ_HOST"  # HACK: hardcoded


def hivemq_communication(outgoing_message, subscribe_topic, publish_topic):
    broker = os.environ[host_key]
    username = os.environ[username_key]
    password = os.environ[password_key]
    # print(f"Connecting to {broker} with username {username} and password {password}")

    received_messages = []  # avoid using nonlocal by using mutable data structure
    message_received_event = threading.Event()
    connected_event = threading.Event()

    def on_connect(client, userdata, flags, rc):
        client.subscribe(subscribe_topic, qos=2)
        connected_event.set()

    def on_message(client, userdata, message):
        received_message = json.loads(message.payload)
        received_messages.append(received_message)
        message_received_event.set()

    client = mqtt_client.Client()
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_message = on_message

    client.tls_set(
        tls_version=mqtt_client.ssl.PROTOCOL_TLS_CLIENT
    )  # Enable TLS with specific version
    client.connect(broker, port=8883)  # Connect to the broker on port 8883
    client.loop_start()

    connected_event.wait(timeout=10)  # Wait for the connection to be established

    client.publish(publish_topic, outgoing_message, qos=2)

    message_received_event.wait(timeout=20)  # Wait for the message to be received

    if not message_received_event.is_set():
        raise TimeoutError("No message received within the specified timeout")

    client.loop_stop()

    assert (
        len(received_messages) == 1
    ), f"Expected 1 message, got {len(received_messages)}"
    received_message = received_messages[0]

    return received_message


"""Developer note:

Within a conda environment, you can run the following commands to set
environment variables persistently in a way that can be read by
os.getenv("VAR_NAME"). This helps while developing the repo locally
instead of needing to run it on GitHub Codespaces.

```
conda env config vars set HIVEMQ_USERNAME=your_username
conda env config vars set HIVEMQ_PASSWORD=your_password
conda env config vars set HIVEMQ_HOST=your_host
conda env config vars set COURSE_ID=your_course_id

(or all in one line, e.g., conda env config vars set HIVEMQ_USERNAME=your_username HIVEMQ_PASSWORD=your_password HIVEMQ_HOST=your_host COURSE_ID=your_course_id)
```
"""
