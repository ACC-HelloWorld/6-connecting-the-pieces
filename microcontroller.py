"""Control the NeoPixel LED """

import sys
import json
import ussl
import asyncio
import ntptime
from uio import StringIO
from time import time, sleep
import urequests_2 as requests  # for MongoDB Data API

# WiFi
from netman import connectWiFi

# Hardware
import machine
from neopixel import NeoPixel
from as7341_sensor import Sensor

# MQTT
from mqtt_as import MQTTClient, config

from my_secrets import (
    SSID,
    PASSWORD,
    COURSE_ID,
    HIVEMQ_HOST,
    HIVEMQ_PASSWORD,
    HIVEMQ_USERNAME,
    DATA_API_KEY,
    ENDPOINT_BASE_URL,
    CLUSTER_NAME,
    DATABASE_NAME,
    COLLECTION_NAME,
)

# Instantiate the LEDs with 1 pixel on Pin 28
neopixels = NeoPixel(machine.Pin(28), 1)

# Instantiate the Sensor class
sensor = Sensor()

# Description: Receive commands from HiveMQ and send dummy sensor data to HiveMQ

connectWiFi(SSID, PASSWORD, country="US")

# To validate certificates, a valid time is required
ntptime.timeout = 5  # type: ignore
ntptime.host = "time.google.com"
try:
    ntptime.settime()
except Exception as e:
    print(f"{e} with {ntptime.host}. Trying again after 5 seconds")
    sleep(5)
    try:
        ntptime.settime()
    except Exception as e:
        print(f"{e} with {ntptime.host}. Trying again with pool.ntp.org")
        sleep(5)
        ntptime.host = "pool.ntp.org"
        ntptime.settime()

print("Obtaining CA Certificate from file")
with open("hivemq-com-chain.der", "rb") as f:
    cacert = f.read()
f.close()

# Local configuration
config.update(
    {
        "ssid": SSID,
        "wifi_pw": PASSWORD,
        "server": HIVEMQ_HOST,
        "user": HIVEMQ_USERNAME,
        "password": HIVEMQ_PASSWORD,
        "ssl": True,
        "ssl_params": {
            "server_side": False,
            "key": None,
            "cert": None,
            "cert_reqs": ussl.CERT_REQUIRED,
            "cadata": cacert,
            "server_hostname": HIVEMQ_HOST,
        },
        "keepalive": 30,
    }
)


# Dummy function for running a color experiment
def run_color_experiment(R, G, B):
    """
    Run a color experiment with the specified RGB values.

    Parameters
    ----------
    R : int
        The red component of the color, between 0 and 255.
    G : int
        The green component of the color, between 0 and 255.
    B : int
        The blue component of the color, between 0 and 255.

    Returns
    -------
    dict
        A dictionary with the sensor data from the experiment.

    Examples
    --------
    >>> run_color_experiment(255, 0, 0)
    {'ch410': 25.5, 'ch440': 51.0, 'ch470': 76.5, 'ch510': 102.0, 'ch550': 127.5, 'ch583': 153.0, 'ch620': 229.5, 'ch670': 255.0} # noqa: E501
    """
    # set the color
    # read the sensor data into a variable named sensor_data
    # clear the color
    ...  # IMPLEMENT

    return sensor_data


def log_experiment(document):
    """
    Sends an experiment document to a specified MongoDB collection.

    This function attempts to send a document to a MongoDB collection via a POST
    request.

    Parameters
    ----------
    document : dict
        The document to be added to the MongoDB collection. This should be a
        dictionary representing the experiment to be logged.

    Returns
    -------
    None

    Examples
    --------
    >>> document = {
    ...     "command": {"R": 255, "G": 0, "B": 0},
    ...     "experiment_id": "a1b2c3",
    ...     "session_id": "d4e5f6",
    ...     "sensor_data": {
    ...         "ch410": 25.5,
    ...         "ch440": 51.0,
    ...         "ch470": 76.5,
    ...         "ch510": 102.0,
    ...         "ch550": 127.5,
    ...         "ch583": 153.0,
    ...         "ch620": 229.5,
    ...         "ch670": 255.0,
    ...     },
    ... }
    >>> log_experiment(document)
    """
    ...  # IMPLEMENT


# MQTT Topics
command_topic = f"{COURSE_ID}/neopixel"
sensor_data_topic = f"{COURSE_ID}/as7341"

print(f"Command topic: {command_topic}")
print(f"Sensor data topic: {sensor_data_topic}")


async def messages(client):  # Respond to incoming messages
    async for topic, msg, retained in client.queue:
        try:
            topic = topic.decode()
            msg = msg.decode()
            retained = str(retained)
            print((topic, msg, retained))

            if topic == command_topic:
                # TODO: Implement message handling logic to run the experiment
                # and publish a dictionary with the original payload dictionary
                # and the sensor data to the sensor data topic. The dictionary
                # should be named payload_data and should be of the form:
                # {
                #     "command": {"R": ..., "G": ..., "B": ...},
                #     "experiment_id": "...",
                #     "session_id": "...",
                #     "sensor_data": {"ch410": ..., "ch440": ..., ..., "ch670": ...},
                # }
                ...  # IMPLEMENT

                # Log the experiment to MongoDB
                log_experiment(payload_data)

        except Exception as e:
            with StringIO() as f:  # type: ignore
                sys.print_exception(e, f)  # type: ignore
                print(f.getvalue())  # type: ignore


async def up(client):  # Respond to connectivity being (re)established
    while True:
        await client.up.wait()  # Wait on an Event
        client.up.clear()
        await client.subscribe(command_topic, 1)  # renew subscriptions


async def main(client):
    await client.connect()
    for coroutine in (up, messages):
        asyncio.create_task(coroutine(client))

    start_time = time()
    # must have the while True loop to keep the program running
    while True:
        await asyncio.sleep(5)
        elapsed_time = round(time() - start_time)
        print(f"Elapsed: {elapsed_time}s")


config["queue_len"] = 5  # Use event interface with specified queue length
MQTTClient.DEBUG = True  # Optional: print diagnostic messages
client = MQTTClient(config)
try:
    asyncio.run(main(client))
finally:
    client.close()  # Prevent LmacRxBlk:1 errors
