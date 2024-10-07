import os
import json
from communication import hivemq_communication
import requests

course_id_key = "COURSE_ID"

# HiveMQ
username_key = "HIVEMQ_USERNAME"
password_key = "HIVEMQ_PASSWORD"
host_key = "HIVEMQ_HOST"

# AWS API Gateway
aws_api_gateway_url_key = "AWS_API_GATEWAY_URL"
aws_api_key_key = "AWS_API_KEY"

def test_env_vars_exist():
    for env_var in [
        course_id_key,
        username_key,
        password_key,
        host_key,
        aws_api_gateway_url_key,
        aws_api_key_key,
    ]:
        assert (
            env_var in os.environ and os.environ[env_var] != ""
        ), f"Environment variable {env_var} does not exist. See README for instructions."
    default_broker = "248cc294c37642359297f75b7b023374.s2.eu.hivemq.cloud"
    assert (
        default_broker not in os.environ[host_key]
    ), f"You must create your own HiveMQ instance rather than use the default, which is {default_broker}"

def test_basic_hivemq_communication():
    outgoing_message = "Test message"
    topic = "/test/topic"
    payload = json.dumps(outgoing_message)
    try:
        received_message = hivemq_communication(payload, topic, topic)
    except Exception as e:
        raise TimeoutError(
            "Double check that your HiveMQ credentials are correct (host, username, password), and that the username/password combination has both subscribe and publish permissions. Refer to the README for instructions."
        ) from e

    assert (
        received_message == outgoing_message
    ), f"Received {received_message} instead of {outgoing_message} on topic {topic}. Check that your HiveMQ instance is set up and that the GitHub secrets are set correctly."  # noqa: E501

def test_aws_api_gateway():
    aws_api_gateway_url = os.environ[aws_api_gateway_url_key]
    aws_api_key = os.environ[aws_api_key_key]
    course_id = os.environ[course_id_key]

    document = {"course_id": course_id, "test": "test"}

    headers = {
        "x-api-key": aws_api_key,
        "Content-Type": "application/json"
    }

    num_retries = 3
    for _ in range(num_retries):
        response = requests.post(
            aws_api_gateway_url,
            headers=headers,
            json=document
        )

        print(f"sending {document} to AWS API Gateway")

        txt = str(response.text)
        status_code = response.status_code

        print(f"Response: ({status_code}), msg = {txt}")

        if status_code == 200:
            print("Added Successfully")
            break

        print("Retrying...")

    assert (
        status_code == 200
    ), f"Received status code {status_code} and message {txt}. Failed to add {document} via AWS API Gateway."

    # Test DELETE request to clean up the test data
    response = requests.delete(f"{aws_api_gateway_url}?course_id={course_id}&test=test", headers=headers)
    assert response.status_code == 200, f"Failed to delete test data from AWS API Gateway. Status code: {response.status_code}"
    
    data = response.json()
    assert any(doc['course_id'] == course_id and doc['test'] == 'test' for doc in data), "Failed to retrieve the test document from AWS API Gateway"


if __name__ == "__main__":
    test_env_vars_exist()
    test_basic_hivemq_communication()
    test_aws_api_gateway()