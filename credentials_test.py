import os
import json
from communication import hivemq_communication
import os
from pymongo.mongo_client import MongoClient
import boto3
from botocore.exceptions import ClientError

course_id_key = "COURSE_ID"

# HiveMQ
username_key = "HIVEMQ_USERNAME"
password_key = "HIVEMQ_PASSWORD"
host_key = "HIVEMQ_HOST"

# general
database_key = "DATABASE_NAME"
collection_key = "COLLECTION_NAME"

# AWS Lambda
lambda_function_url_key = "LAMBDA_FUNCTION_URL"


# For PyMongo
atlas_uri_key = "ATLAS_URI"


def test_env_vars_exist():
    for env_var in [
        course_id_key,
        username_key,
        password_key,
        host_key,
        database_key,
        collection_key,
        lambda_function_url_key,
        atlas_uri_key,
    ]:
        assert (
            env_var in os.environ
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


def test_connection():
    # Create a new client and connect to the server
    atlas_uri = os.environ[atlas_uri_key]
    client = MongoClient(atlas_uri)

    # Send a ping to confirm a successful connection
    try:
        client.admin.command("ping")
        print("Pinged your deployment. You successfully connected to MongoDB!")
        success = True
    except Exception as e:
        success = False
        print(e)

    assert success, f"""Could not connect to MongoDB using the following URI: {atlas_uri}. 
    The URI should be of the format mongodb+srv://<username>:<password>@<cluster_name>.<cluster_id>.mongodb.net/?retryWrites=true&w=majority 
    where your cluster name and cluster ID can be found using the 'Connect' button interface on MongoDB Atlas. 
    For example, if your username is `sgbaird`, password is `HGzZNsQ3vBLKrZXXF`, cluster name is `test-cluster`, and cluster ID is `c5jgpni`, 
    then your URI would be: mongodb+srv://sgbaird:HGzZNsQ3vBLKrZXXF@test-cluster.c5jgpni.mongodb.net/?retryWrites=true&w=majority.
    Please check your environment variables and ensure your MongoDB database and collection are set up correctly."""

    # upload a test document
    db = client[os.environ[database_key]]
    collection = db[os.environ[collection_key]]
    test_document = {"test": "test"}
    collection.insert_one(test_document)
    print(f"Inserted a test document into the {os.environ[collection_key]} collection.")

    # read the test document
    test_document = collection.find_one(test_document)
    print(f"Found the test document in the {os.environ[collection_key]} collection.")

    # delete the test document
    collection.delete_one(test_document)
    print(
        f"Deleted the test document from the {os.environ[collection_key]} collection."
    )

    # close the connection
    client.close()


def test_lambda_function_url():
    LAMBDA_FUNCTION_URL = os.environ[lambda_function_url_key]
    DATABASE_NAME = os.environ[database_key]
    COLLECTION_NAME = os.environ[collection_key]
    COURSE_ID = os.environ[course_id_key]

    document = {"course_id": COURSE_ID}

    payload = {
        "database": DATABASE_NAME,
        "collection": COLLECTION_NAME,
        "document": document,
    }

    print(
        f"sending {document} to {DATABASE_NAME}:{COLLECTION_NAME} via Lambda function URL"
    )

    response = requests.post(LAMBDA_FUNCTION_URL, json=payload)

    txt = str(response.text)
    status_code = response.status_code

    print(f"Response: ({status_code}), msg = {txt}")

    if status_code == 200:
        print("Added Successfully")

    assert (
        status_code == 200
    ), f"Received status code {status_code} and message {txt}. Failed to add {document} to {DATABASE_NAME}:{COLLECTION_NAME} via Lambda function URL."


def test_aws_credentials():
    try:
        # Create a DynamoDB client
        dynamodb = boto3.client('dynamodb',
                                aws_access_key_id=os.environ[aws_access_key_id_key],
                                aws_secret_access_key=os.environ[aws_secret_access_key_key],
                                region_name=os.environ[aws_region_key])
        
        # Try to describe the table
        table_name = os.environ[dynamodb_table_name_key]
        response = dynamodb.describe_table(TableName=table_name)
        
        print(f"Successfully connected to DynamoDB table: {table_name}")
        
        # Test item insertion
        test_item = {
            'id': {'S': 'test-item'},
            'data': {'S': 'test-data'}
        }
        dynamodb.put_item(TableName=table_name, Item=test_item)
        print("Successfully inserted test item into DynamoDB table")
        
        # Test item retrieval
        response = dynamodb.get_item(TableName=table_name, Key={'id': {'S': 'test-item'}})
        assert response['Item']['data']['S'] == 'test-data', "Retrieved item does not match inserted item"
        print("Successfully retrieved test item from DynamoDB table")
        
        # Delete test item
        dynamodb.delete_item(TableName=table_name, Key={'id': {'S': 'test-item'}})
        print("Successfully deleted test item from DynamoDB table")
        
    except ClientError as e:
        print(f"Error: {e}")
        assert False, f"Failed to connect to DynamoDB or perform operations. Check your AWS credentials and DynamoDB table name."

if __name__ == "__main__":
    test_env_vars_exist()
    test_basic_hivemq_communication()
    test_connection()
    test_lambda_function_url()
