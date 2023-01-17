from http import HTTPStatus
import dataclasses
import os
import json

import pytest
from requests.exceptions import HTTPError

from fitbit.constants import TOKEN_URL
import fitbit.authorization as auth
from tests.fixtures import api_credentials, api_token, local_token_manager


###########################################
# Perform tests on the Fitbit Token class #
###########################################
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


############################################
# Perform Tests on LocalTokenManager Class #
############################################
def test_return_path_parameters(local_token_manager) -> None:
    parameters = {
        "directory": "test_path/credentials",
        "name": "test_save_local_credentials",
        "make_directory": False,
    }
    expected_result = (
        parameters["directory"],
        parameters["name"],
        parameters["make_directory"],
    )

    hidden_function = local_token_manager._LocalTokenManager__return_path_parameters

    assert hidden_function(parameters) == expected_result
    assert hidden_function() == ("local_data", "token", True)
    assert hidden_function({}) == ("local_data", "token", True)


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

    credentials_parameters = {"directory": directory, "name": name}
    local_token_manager = auth.LocalTokenManager(
        credentials_parameters=credentials_parameters, load_credentials=True
    )

    assert local_token_manager.credentials == api_credentials


def test_save_local_token(tmp_path, local_token_manager, api_token) -> None:
    """
    Test the save_local_token function to check that it saves the file to correct spot
    """
    name = "test_save_local_token"
    directory = f"{tmp_path}/tokens"
    parameters = {"name": name, "directory": directory}

    local_token_manager.save_token(api_token, parameters)

    full_path = f"{directory}/{name}.json"
    assert os.path.exists(full_path)


def test_save_local_token_bad_directory(api_token, local_token_manager) -> None:
    """
    Test the save_token_local function to check that it saves the file to correct spot
    """
    directory = "Source/FitbitExtract/tests/bad_directory"
    parameters = {"directory": directory, "make_directory": False}

    with pytest.raises(
        FileNotFoundError, match="\\[Errno 2\\] No such file or directory:.*"
    ):
        local_token_manager.save_token(api_token, parameters)


def test_load_local_token(tmp_path, local_token_manager, api_token) -> None:
    """
    Test the load local token function to ensure it returns expected result
    """
    name = "test_save_local_token"
    directory = f"{tmp_path}/tokens"
    parameters = {"name": name, "directory": directory}

    local_token_manager.save_token(api_token, parameters)

    credentials = local_token_manager.load_token(parameters)

    assert credentials == api_token


def test_refresh_token(requests_mock, local_token_manager, api_token) -> None:
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

    access_token = local_token_manager.refresh_token(api_token)
    api_token_check = dataclasses.replace(api_token)
    api_token_check.access_token_isvalid = True
    assert access_token == api_token_check


def test_refresh_token_bad_status(
    requests_mock, api_token, local_token_manager
) -> None:
    """
    Test the get_access_token function to check that it returns a response for when http status is not OK
    """
    requests_mock.post(
        TOKEN_URL,
        json={"access_token": "test_access_token"},
        status_code=HTTPStatus.BAD_GATEWAY,
    )

    with pytest.raises(HTTPError):
        local_token_manager.refresh_token(api_token)


def test_refresh_token_not_credentials(api_token) -> None:
    """
    Test the get_access_token function to check that it returns a response for when http status is not OK
    """
    bad_local_token_mabager = auth.LocalTokenManager()

    with pytest.raises(AttributeError, match="credentials attribute has not been set"):
        bad_local_token_mabager.refresh_token(api_token)
