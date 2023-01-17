from http import HTTPStatus

import pytest

import fitbit.authorization as auth
import fitbit.caller as caller


############################################
# Ceate a testing requester to simulate API #
############################################
class TestingFitbitRequester:
    def __init__(self) -> None:
        self.response = '{"field1": "value1", "field2": 2, "field3": "value3"}'
        self.http_status = HTTPStatus.OK

    def make_request(
        self, url: str, headers: dict, body: dict
    ) -> tuple[str, HTTPStatus]:
        return self.response, self.http_status


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
def local_response_saver(tmp_path) -> caller.FitbitResponseSaver:
    base_directory = tmp_path

    return caller.LocalResponseSaver(base_directory)


@pytest.fixture()
def fitbitcaller(
    api_token, local_response_saver, local_token_manager
) -> caller.FitBitCaller:
    """Pytest fixture for a token manager for testing

    Returns:
        TokenManager: an instance of a token manager used for testing
    """
    requester = TestingFitbitRequester()

    return caller.FitBitCaller(
        api_token, local_response_saver, requester, local_token_manager
    )
