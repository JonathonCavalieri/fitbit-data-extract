from http import HTTPStatus
import json
import os
import pytest
import uuid
import dataclasses

from google.cloud import storage

import fitbit.authorization as auth
import fitbit.caller as caller
import fitbit.savers as savers

###############################
# Get GCP objects for testing #
###############################
CONFIG_DIRECTORY = "config.json"
if not os.path.exists(CONFIG_DIRECTORY):
    raise Exception("No config.json file found")

with open(CONFIG_DIRECTORY, "r", encoding="utf-8") as config_file:
    config_dictionary = json.load(config_file)

if "testing_gcp_project" not in config_dictionary:
    raise KeyError("Please create")

GCP_PROJECT_ID = config_dictionary["testing_gcp_project"]


@pytest.fixture(scope="session")
def gcp_storage_client() -> storage.Client:
    return storage.Client(GCP_PROJECT_ID)


############################################
# Ceate a testing requester to simulate API #
############################################
class TestingFitbitRequester:
    def __init__(self) -> None:
        self.response = '{"field1": "value1", "field2": 2, "field3": "value3"}'
        self.http_status = HTTPStatus.OK
        self.called = 0
        self.OK_after = 1

    def make_request(  # pylint: disable=W0613
        self, method: str, url: str, headers: dict, body: dict
    ) -> tuple[str, HTTPStatus]:
        self.called += 1
        if self.called > self.OK_after:
            self.http_status = HTTPStatus.OK

        return self.response, self.http_status


class TestingTokenManager:
    """
    A fake token manager used for testings
    """

    def __init__(
        self, token: auth.FitbitToken, credentials: auth.FitbitAppCredentials
    ) -> None:
        self.return_data = token
        self.credentials = credentials
        self.return_data.access_token_isvalid = True

    def refresh_token(self, token: auth.FitbitToken) -> auth.FitbitToken:
        """Refreshes a fitbit access token"""
        return self.return_data

    def load_credentials(self, parameters: dict) -> None:
        """Load Credentials from storage"""

    def load_token(self, parameters: dict) -> auth.FitbitToken:
        """Load API Token from storage"""
        return self.return_data

    def save_token(self, token: auth.FitbitToken, parameters: dict = None) -> None:
        """Save API Token to storage"""


##########################################
# Create GCP Bucket for testing purposes #
##########################################
@pytest.fixture(scope="session")
def gcp_response_saver(gcp_storage_client) -> savers.GCPResponseSaver:
    session_id = uuid.uuid1()
    bucket_name = f"testing_bucket_{session_id}"
    gcp_storage_client.create_bucket(bucket_name)
    response_saver = savers.GCPResponseSaver(bucket_name, GCP_PROJECT_ID)
    yield response_saver

    response_saver.bucket.delete(force=True)


############################################
# Create fixture objects to use in testing #
############################################
@pytest.fixture()
def api_token() -> auth.FitbitToken:
    """fixture for api token for testing

    Returns:
        FitbitToken: test api token object
    """
    return auth.FitbitToken(
        "test_refresh_token", "test_access_token", "test_scope", "test_user"
    )


@pytest.fixture()
def api_credentials() -> auth.FitbitAppCredentials:
    """Pytest fixture for api credentials for testing

    Returns:
        FitbitAppCredentials: test api credentials object
    """
    return auth.FitbitAppCredentials("test_client_id", "test_client_secret")


@pytest.fixture()
def local_token_manager(tmp_path, api_credentials) -> auth.TokenManager:
    """Pytest fixture for a token manager for testing

    Returns:
        TokenManager: an instance of a token manager used for testing
    """
    credentials_parameters = {
        "directory": f"{tmp_path}/tokens",
        "name": "test_save_local_token",
    }

    token_parameters = {
        "directory": f"{tmp_path}/credentials",
        "name": "test_save_local_credentials",
    }

    return auth.LocalTokenManager(
        credentials_parameters=credentials_parameters,
        token_parameters=token_parameters,
        credentials=api_credentials,
    )


@pytest.fixture()
def testing_token_manager(api_credentials) -> auth.TokenManager:
    refreshed_token = auth.FitbitToken(
        "refreshed", "test_access_token", "test_scope", "test_user"
    )
    return TestingTokenManager(refreshed_token, api_credentials)


@pytest.fixture()
def local_response_saver(tmp_path) -> caller.FitbitResponseSaver:
    base_directory = tmp_path

    return savers.LocalResponseSaver(base_directory)


@pytest.fixture()
def fitbitcaller(
    api_token, local_response_saver, testing_token_manager
) -> caller.FitBitCaller:
    """Pytest fixture for a token manager for testing

    Returns:
        TokenManager: an instance of a token manager used for testing
    """
    requester = TestingFitbitRequester()

    return caller.FitBitCaller(
        api_token, local_response_saver, requester, testing_token_manager
    )
