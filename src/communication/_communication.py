import os
import json
from paho.mqtt import client as mqtt_client
import threading

# Use more descriptive environment variable names
USERNAME_KEY = "AWS_IOT_USERNAME"
PASSWORD_KEY = "AWS_IOT_PASSWORD"
HOST_KEY = "AWS_IOT_ENDPOINT"

def hivemq_communication(outgoing_message, subscribe_topic, publish_topic):
    broker = os.environ[HOST_KEY]
    username = os.environ[USERNAME_KEY]
    password = os.environ[PASSWORD_KEY]

    received_messages = []
    message_received_event = threading.Event()
    connected_event = threading.Event()

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to AWS IoT Core")
            client.subscribe(subscribe_topic, qos=1)
            connected_event.set()
        else:
            print(f"Failed to connect, return code {rc}")

    def on_message(client, userdata, message):
        received_message = json.loads(message.payload)
        received_messages.append(received_message)
        message_received_event.set()

    client = mqtt_client.Client()
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_message = on_message

    # AWS IoT Core specific TLS configuration
    client.tls_set(certfile=os.environ.get('AWS_IOT_CERTIFICATE'),
                   keyfile=os.environ.get('AWS_IOT_PRIVATE_KEY'),
                   ca_certs=os.environ.get('AWS_IOT_ROOT_CA'))

    client.connect(broker, port=8883)
    client.loop_start()

    if not connected_event.wait(timeout=10):
        raise ConnectionError("Failed to connect to AWS IoT Core")

    client.publish(publish_topic, outgoing_message, qos=1)

    if not message_received_event.wait(timeout=20):
        raise TimeoutError("No message received within the specified timeout")

    client.loop_stop()

    assert len(received_messages) == 1, f"Expected 1 message, got {len(received_messages)}"
    return received_messages[0]

# Update the developer note
"""Developer note:

To set up AWS IoT Core credentials in your conda environment:

conda env config vars set AWS_IOT_USERNAME=your_username
conda env config vars set AWS_IOT_PASSWORD=your_password
conda env config vars set AWS_IOT_ENDPOINT=your_aws_iot_endpoint
conda env config vars set AWS_IOT_CERTIFICATE=/path/to/certificate.pem.crt
conda env config vars set AWS_IOT_PRIVATE_KEY=/path/to/private.pem.key
conda env config vars set AWS_IOT_ROOT_CA=/path/to/AmazonRootCA1.pem
conda env config vars set COURSE_ID=your_course_id
"""