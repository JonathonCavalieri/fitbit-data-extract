from http import HTTPStatus
import dataclasses
import os
import json
import fitbit.authorization as auth
import pytest
from fitbit.constants import TOKEN_URL
from requests.exceptions import HTTPError

# Create fixture objects to use in testing
@pytest.fixture(scope="module")
def api_token() -> auth.FitbitToken:
    """fixture for api token for testing

    Returns:
        FitbitToken: test api token object
    """
    return auth.FitbitToken(
        "test_refresh_token", "test_access_token", "test_scope", "test_user"
    )


@pytest.fixture(scope="module")
def api_credentials() -> auth.FitbitAppCredentials:
    """Pytest fixture for api credentials for testing

    Returns:
        FitbitAppCredentials: test api credentials object
    """
    return auth.FitbitAppCredentials("test_client_id", "test_client_secret")


# Perform Tests
def test_save_local_token(tmp_path, api_token) -> None:
    """
    Test the save_local_token function to check that it saves the file to correct spot
    """
    name = "test_save_local_token"
    directory = f"{tmp_path}/tokens"
    auth.save_local_token(api_token, directory=directory, name=name)
    full_path = f"{directory}/{name}.json"
    assert os.path.exists(full_path)


def test_save_local_token_bad_directory(api_token) -> None:
    """
    Test the save_token_local function to check that it saves the file to correct spot
    """
    directory = "Source/FitbitExtract/tests/bad_directory"

    with pytest.raises(
        FileNotFoundError, match="\\[Errno 2\\] No such file or directory:.*"
    ):
        auth.save_local_token(api_token, directory=directory, make_directory=False)


def test_load_local_token(tmp_path, api_token) -> None:
    """
    Test the load local token function to ensure it returns expected result
    """

    directory = f"{tmp_path}/tokens"
    auth.save_local_token(api_token, directory=directory)

    credentials = auth.load_local_token(directory, "token")

    assert credentials == api_token


def test_load_local_credentials(tmp_path, api_credentials) -> None:
    """
    Test the load local credentials function to ensure it returns expected result
    """

    credentials_file = {
        "client_id": api_credentials.client_id,
        "client_secret": api_credentials.client_secret,
        "scope": "activity weight heartrate",
    }
    directory = f"{tmp_path}"
    name = "credentials"
    full_path = f"{directory}/{name}.json"
    with open(full_path, "w", encoding="utf-8") as file:
        json.dump(credentials_file, file, ensure_ascii=False, indent=4)
    credentials = auth.load_local_credentials(directory, "credentials")

    assert credentials == api_credentials


def test_fitbittoken_return_authorization(api_token) -> None:
    """
    Tests that the data class returns the expected header for a given access token
    """
    api_token_check = dataclasses.replace(api_token)
    api_token_check.access_token_isvalid = True
    expected_header = f"Bearer {api_token_check.access_token}"
    assert expected_header == api_token_check.return_authorization()


def test_fitbittoken_return_authorization_invalid(api_token) -> None:
    """
    Tests that the data class returns the expected header for a given access token
    """
    with pytest.raises(ValueError, match="Access token is invalid"):
        api_token.return_authorization()


def test_refresh_access_token(requests_mock, api_token, api_credentials) -> None:
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

    access_token = auth.refresh_access_token(api_token, api_credentials)
    api_token_check = dataclasses.replace(api_token)
    api_token_check.access_token_isvalid = True
    assert access_token == api_token_check


def test_get_access_token_bad_status(requests_mock, api_token, api_credentials) -> None:
    """
    Test the get_access_token function to check that it returns a response for when http status is not OK
    """
    requests_mock.post(
        TOKEN_URL,
        json={"access_token": "test_access_token"},
        status_code=HTTPStatus.BAD_GATEWAY,
    )

    with pytest.raises(HTTPError):
        auth.refresh_access_token(api_token, api_credentials)
