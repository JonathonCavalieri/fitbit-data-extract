from typing import Tuple
import uuid
import pytest
import json
import re
from google.cloud import storage, bigquery, secretmanager
from helper.functions import get_config_parameter
from fitbit.caller import EndpointParameters
from fitbit import savers, messengers, loaders
from fitbit.authorization import CloudTokenManager, CloudTokenManagerParameters
from http import HTTPStatus
import dataclasses

from requests.exceptions import HTTPError

from fitbit.constants import TOKEN_URL
from tests.fixtures import api_token

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


@pytest.fixture(scope="session")
def gcp_loader(gcp_response_saver) -> Tuple[loaders.GCPDataLoader, str]:
    """
    A testing GCP Loader object. This creates a GCP bucket in the test project id
    specified in the config that will be deleted after running tests
    """
    session_id = uuid.uuid1()
    bucket_name = gcp_response_saver.bucket_name
    dataset_name = f"testing_dataset_{session_id}".replace("-", "_")
    table_name = f"testing_table_{session_id}".replace("-", "_")
    table_ref = f"{GCP_PROJECT_ID}.{dataset_name}.{table_name}"

    bigquery_client = bigquery.Client(project=GCP_PROJECT_ID)
    dataset = bigquery_client.create_dataset(dataset_name)
    schema = [
        bigquery.SchemaField("test_string_column", "STRING"),
        bigquery.SchemaField("test_int_column", "INTEGER"),
    ]
    table = bigquery.Table(table_ref, schema=schema)
    table = bigquery_client.create_table(table)

    loader = loaders.GCPDataLoader(GCP_PROJECT_ID, bucket_name, dataset_name)
    yield loader, table_name

    bigquery_client.delete_dataset(dataset, delete_contents=True)


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


def test_pubsub_prep_message_all(pubsub_messenger) -> None:
    """test the prep_message method from PubSubMessenger class"""
    endpoints = ["all"]
    user_id = "TESTUSER"
    date = "2023-01-18"

    messages = pubsub_messenger.prep_message(endpoints, user_id, date)
    expected_message = (
        b'{"user_id": "TESTUSER", "date": "2023-01-18", "endpoints": ["all"]}'
    )
    assert messages == expected_message


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


################################
# Test the GCPDataLoader Class #
################################
def test_gcp_loader_extract(gcp_response_saver, gcp_loader) -> None:
    "Test the extract method of the GCPDataLoader class"

    loader, _ = gcp_loader
    dictionary = {"field1": "value1", "field2": 2, "field3": "value3"}
    fake_json_data = json.dumps(dictionary)
    folder = "loader"
    file_format = "json"
    file_name = "test_save_file"
    gcp_response_saver.save(fake_json_data, folder, file_name, file_format)
    blob_name = f"{folder}/{file_name}.{file_format}"

    data = loader.extract(blob_name)

    assert data == dictionary


def test_gcp_loader_extract_tcx(gcp_response_saver, gcp_loader) -> None:
    "Test the extract method of the GCPDataLoader class"
    loader, _ = gcp_loader
    fake_tcx_data = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <TrainingCenterDatabase xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2">
        <Activities>
            <Activity Sport="Running">
                <Id>2022-10-13T07:07:03.000+11:00</Id>
                <Lap StartTime="2022-10-13T07:07:03.000+11:00">
                    <TotalTimeSeconds>414.0</TotalTimeSeconds>
                    <DistanceMeters>1000.0</DistanceMeters>
                    <Calories>67</Calories>
                    <Intensity>Active</Intensity>
                    <TriggerMethod>Manual</TriggerMethod>
                    <Track>
                        <Trackpoint>
                            <Time>2022-10-13T07:07:03.000+11:00</Time>
                            <Position>
                                <LatitudeDegrees>-33.89690887928009</LatitudeDegrees>
                                <LongitudeDegrees>151.19783425331116</LongitudeDegrees>
                            </Position>
                            <AltitudeMeters>44.48640000833932</AltitudeMeters>
                            <DistanceMeters>0.0</DistanceMeters>
                            <HeartRateBpm>
                                <Value>90</Value>
                            </HeartRateBpm>
                        </Trackpoint>
                    </Track>
                </Lap>
                <Creator xsi:type="Device_t" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <UnitId>0</UnitId>
                    <ProductID>0</ProductID>
                </Creator>
            </Activity>
        </Activities>
    </TrainingCenterDatabase>
    """
    folder = "loader"
    file_format = "tcx"
    file_name = "test_save_file_tcx"
    gcp_response_saver.save(fake_tcx_data, folder, file_name, file_format)
    blob_name = f"{folder}/{file_name}.{file_format}"
    results = loader.extract(blob_name)

    assert results["xml_data"] == fake_tcx_data


def test_gcp_loader_extract_bad_format(gcp_response_saver, gcp_loader) -> None:
    "Test the extract method of the GCPDataLoader class for bad file format"
    loader, _ = gcp_loader
    dictionary = {"field1": "value1", "field2": 2, "field3": "value3"}
    fake_json_data = str(dictionary)
    folder = "loader"
    file_format = "csv"
    file_name = "test_save_file"
    blob_name = f"{folder}/{file_name}.{file_format}"
    gcp_response_saver.save(fake_json_data, folder, file_name, file_format)

    with pytest.raises(ValueError, match=f"file type .{file_format} is not supported"):
        loader.extract(blob_name)


def test_gcp_loader_load(gcp_loader) -> None:
    "Test the load method of the GCPDataLoader class"
    loader, table_name = gcp_loader
    data = [
        {"test_string_column": "value1", "test_int_column": 10},
        {"test_string_column": "value2", "test_int_column": 5},
    ]
    loader.load(data, table_name)
    query = loader.bigquery_client.query(
        f"SELECT * FROM `{loader.project_id}.{loader.dataset_name}.{table_name}`"
    )
    results = query.result()

    results = [dict(result) for result in results]

    assert data == results


def test_gcp_loader_load_no_data(gcp_loader) -> None:
    "Test the load method of the GCPDataLoader class for no data sent"
    loader, _ = gcp_loader

    assert loader.load([], "nothing") is None
    assert loader.load(None, "nothing") is None


def test_gcp_loader_load_gcp_error(gcp_loader) -> None:
    "Test the load method of the GCPDataLoader class"
    loader, table_name = gcp_loader
    data = [
        {"test_string_column": "value1", "test_int_column": "bad_value"},
        {"test_string_column": "value2", "test_int_column": 5},
    ]

    errors = [
        {
            "index": 0,
            "errors": [
                {
                    "reason": "invalid",
                    "location": "test_int_column",
                    "debugInfo": "",
                    "message": "Cannot convert value to integer (bad value): bad_value",
                }
            ],
        },
        {
            "index": 1,
            "errors": [
                {"reason": "stopped", "location": "", "debugInfo": "", "message": ""}
            ],
        },
    ]
    expected_error_string = re.escape(
        f"Encountered errors while inserting rows into table: {table_name} \nErrors:\n {errors}"
    )
    with pytest.raises(ValueError, match=expected_error_string):
        loader.load(data, table_name)


################################
# Test the CloudTokenManager Class #
################################
from unittest.mock import patch, Mock
from cryptography.fernet import Fernet

FERNET_KEY = Fernet.generate_key()


# def load_secret_from_gcp_test(cls, *args, **kwargs) -> bytes:
#     return FERNET_KEY


def fake_secret_version(cls, *args, **kwargs):
    response = Mock()
    response.payload.data = FERNET_KEY
    return response


@pytest.fixture(scope="session")
def cloud_token_manager(gcp_response_saver):
    with patch.object(
        secretmanager.SecretManagerServiceClient,
        "access_secret_version",
        new=fake_secret_version,
    ):
        token_manager = CloudTokenManager(
            GCP_PROJECT_ID, gcp_response_saver.bucket_name, "test_user"
        )
        yield token_manager


def test_gcp_token_manager_refresh_token(
    requests_mock, api_token, cloud_token_manager
) -> None:
    """
    Test the refresh_access_token function to check that it returns a response for http OK
    """
    requests_mock.post(
        TOKEN_URL,
        json={
            "access_token": api_token.access_token,
            "refresh_token": api_token.refresh_token,
            "scope": api_token.scope,
            "user_id": api_token.user_id,
        },
        status_code=HTTPStatus.OK,
    )

    access_token = cloud_token_manager.refresh_token(api_token)
    api_token_check = dataclasses.replace(api_token)
    api_token_check.access_token_isvalid = True
    assert access_token == api_token_check


def test_gcp_token_manager_refresh_token_bad_status(
    requests_mock, api_token, cloud_token_manager
) -> None:
    """
    Test the get_access_token function to check that it returns
     a response for when http status is not OK
    """
    requests_mock.post(
        TOKEN_URL,
        json={"access_token": "test_access_token"},
        status_code=HTTPStatus.BAD_GATEWAY,
    )

    with pytest.raises(HTTPError):
        cloud_token_manager.refresh_token(api_token)


def test_refresh_token_not_credentials(api_token, gcp_response_saver) -> None:
    """
    Test the get_access_token function to check that it
    returns a response for when http status is not OK
    """
    with patch.object(
        secretmanager.SecretManagerServiceClient,
        "access_secret_version",
        new=fake_secret_version,
    ):
        token_manager = CloudTokenManager(
            GCP_PROJECT_ID,
            gcp_response_saver.bucket_name,
            "test_user",
            parameters=CloudTokenManagerParameters(),
        )
        token_manager.credentials = None
        with pytest.raises(
            AttributeError, match="credentials attribute has not been set"
        ):
            token_manager.refresh_token(api_token)


def test_gcp_token_manager_save_load(api_token, cloud_token_manager) -> None:
    """
    Test the save and load functions of cloud token manager
    """
    cloud_token_manager.save_token(api_token)
    result = cloud_token_manager.load_token()

    assert api_token == result


def test_gcp_token_manager_load_secret(cloud_token_manager):
    secret = cloud_token_manager._load_secret_from_gcp("dummy")
    assert secret == FERNET_KEY
