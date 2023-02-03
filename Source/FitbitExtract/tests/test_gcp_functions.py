import uuid
import pytest

from google.cloud import storage

from helper.functions import get_config_parameter
from fitbit.caller import EndpointParameters
from fitbit import savers, messengers

##################################
# Get GCP parameters for testing #
##################################
CONFIG_DIRECTORY = "config.json"
GCP_PROJECT_ID = get_config_parameter(CONFIG_DIRECTORY, "testing_gcp_project")
GCP_PUBSUB_TOPIC = get_config_parameter(CONFIG_DIRECTORY, "testing_pub_sub_topic_name")


###########################################
# Create GCP resource for testing purposes #
###########################################
@pytest.fixture(scope="session")
def gcp_storage_client() -> storage.Client:
    """A GCS storage client fixture for testing for the testing project specified in config file"""
    return storage.Client(GCP_PROJECT_ID)


@pytest.fixture(scope="session")
def gcp_response_saver(gcp_storage_client) -> savers.GCPResponseSaver:
    """
    A testing GCP response saver object. This creates a GCP bucket in the test project id
    specified in the config that will be deleted after running tests
    """
    session_id = uuid.uuid1()
    bucket_name = f"testing_bucket_{session_id}"
    gcp_storage_client.create_bucket(bucket_name)
    response_saver = savers.GCPResponseSaver(bucket_name, GCP_PROJECT_ID)
    yield response_saver

    response_saver.bucket.delete(force=True)


@pytest.fixture(scope="session")
def pubsub_messenger() -> messengers.PubSubMessenger:
    """Local Messenger fixture for Testing"""
    return messengers.PubSubMessenger(GCP_PROJECT_ID, GCP_PUBSUB_TOPIC)


#################################
# Testing PubSubMessenger Class #
#################################
def test_pubsub_prep_message(pubsub_messenger) -> None:
    """test the prep_message method from PubSubMessenger class"""
    endpoints = [EndpointParameters("test1"), EndpointParameters("test2")]
    user_id = "TESTUSER"
    date = "2023-01-18"

    messages = pubsub_messenger.prep_message(endpoints, user_id, date)
    expected_message = b'{"user_id": "TESTUSER", "date": "2023-01-18", "endpoints": [{"name": "test1", "method": "GET", "response_format": "json", "url_kwargs": {}, "body": {}, "headers": {}}, {"name": "test2", "method": "GET", "response_format": "json", "url_kwargs": {}, "body": {}, "headers": {}}]}'
    assert messages == expected_message


def test_pubsub_prep_message_no_data(pubsub_messenger) -> None:
    """test the prep_message method from PubSubMessenger class when no data is provided"""
    user_id = "TESTUSER"
    date = "2023-01-18"
    endpoints = []
    messages = pubsub_messenger.prep_message(endpoints, user_id, date)
    assert messages is None


def test_pubsub_send_message(pubsub_messenger, capsys) -> None:
    """ "test the send_message method from PubSubMessenger class"""
    message = b"Testing Message"
    response = pubsub_messenger.send_message(message)
    captured = capsys.readouterr()
    expected_value = f"Publishing message {message} to topic {pubsub_messenger.topic_name} message id: {response}\n"
    assert captured.out == expected_value
    assert response


###################################
# Test the GCPResponseSaver Class #
###################################


def test_gcp_response_saver_json(gcp_response_saver) -> None:
    """Test the GCP save object with saving a json file"""
    fake_json_data = '{"field1": "value1", "field2": 2, "field3": "value3"}'
    folder = "data"
    file_format = "json"
    file_name = "test_save_file"

    gcp_response_saver.save(fake_json_data, folder, file_name, file_format)
    blob_name = f"{folder}/{file_name}.{file_format}"
    blob = gcp_response_saver.bucket.blob(blob_name)

    assert blob.exists
