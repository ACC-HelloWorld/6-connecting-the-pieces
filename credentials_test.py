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
cluster_name_key = "CLUSTER_NAME"

# AWS specific
aws_access_key_id_key = "AWS_ACCESS_KEY_ID"
aws_secret_access_key_key = "AWS_SECRET_ACCESS_KEY"
aws_region_key = "AWS_REGION"
dynamodb_table_name_key = "DYNAMODB_TABLE_NAME"

# For PyMongo
connection_string_key = "CONNECTION_STRING"


def test_env_vars_exist():
    for env_var in [
        course_id_key,
        username_key,
        password_key,
        host_key,
        database_key,
        collection_key,
        cluster_name_key,
        aws_access_key_id_key,
        aws_secret_access_key_key,
        aws_region_key,
        dynamodb_table_name_key,
        connection_string_key,
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


def test_connection():
    # Create a new client and connect to the server
    connection_string = os.environ[connection_string_key]
    client = MongoClient(connection_string)

    # Send a ping to confirm a successful connection
    try:
        client.admin.command("ping")
        print("Pinged your deployment. You successfully connected to MongoDB!")
        success = True
    except Exception as e:
        success = False
        print(e)

    assert success, f"""Could not connect to MongoDB using the following URI: {connection_string}. 
    The URI should be of the format mongodb+srv://<username>:<password>@<cluster_name>.<cluster_id>.mongodb.net/?retryWrites=true&w=majority 
    where your cluster name and cluster ID can be found using the 'Connect' button interface on MongoDB Atlas. 
    For example, if your username is `test-user-find-only`, password is `HGzZNsQ3vBLKrXXF`, cluster name is `test-cluster`, and cluster ID is `c5jgpni`, 
    then your URI would be: mongodb+srv://sgbaird:HGzZNsQ3vBLKrXXF@test-cluster.c5jgpni.mongodb.net/?retryWrites=true&w=majority.
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


def test_data_api():
    endpoint_base_url = os.environ[endpoint_base_url_key]
    data_api_key = os.environ[data_api_key_key]
    cluster_name = os.environ[cluster_name_key]
    database_name = os.environ[database_key]
    collection_name = os.environ[collection_key]
    course_id = os.environ[course_id_key]

    document = {"course_id": course_id}

    endpoint_url = f"{endpoint_base_url}/action/insertOne"

    num_retries = 3
    for _ in range(num_retries):
        response = requests.post(
            endpoint_url,
            headers={"api-key": data_api_key},
            json={
                "dataSource": cluster_name,
                "database": database_name,
                "collection": collection_name,
                "document": document,
            },
        )

        print(
            f"sending {document} to {cluster_name}:{database_name}:{collection_name} via {endpoint_base_url}"
        )

        txt = str(response.text)
        status_code = response.status_code

        print(f"Response: ({status_code}), msg = {txt}")

        if status_code == 201:
            print("Added Successfully")
            break

        print("Retrying...")

    assert (
        status_code == 201
    ), f"Received status code {status_code} and message {txt}. Failed to add {document} to {cluster_name}:{database_name}:{collection_name} via {endpoint_base_url}."


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
    test_connection()  # This still tests MongoDB connection
    test_aws_credentials()  # New test for AWS credentials
