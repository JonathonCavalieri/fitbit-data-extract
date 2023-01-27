from http import HTTPStatus
import dataclasses
import os
import json

import pytest
from requests.exceptions import HTTPError

from fitbit.constants import TOKEN_URL
import fitbit.authorization as auth
from tests.fixtures import (  # pylint: disable=W0611
    api_credentials,
    api_token,
    local_token_manager,
)


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
def test_local_token_manager_default_init():
    local_token_manager = auth.LocalTokenManager()
    assert local_token_manager.parameters == auth.LocalTokenManagerParameters()


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

    credentials_parameters = auth.LocalTokenManagerParameters(
        credentials_directory=directory, credentials_name=name, load_credentials=True
    )
    local_token_manager = auth.LocalTokenManager(parameters=credentials_parameters)

    assert local_token_manager.credentials == api_credentials


def test_save_local_token(local_token_manager, api_token) -> None:
    """
    Test the save_local_token function to check that it saves the file to correct spot
    """
    name = local_token_manager.parameters.token_name
    directory = local_token_manager.parameters.token_directory

    local_token_manager.save_token(api_token)

    full_path = f"{directory}/{name}.json"
    assert os.path.exists(full_path)


def test_save_local_token_bad_directory(api_token, local_token_manager) -> None:
    """
    Test the save_token_local function to check that it saves the file to correct spot
    """
    local_token_manager.parameters.token_directory = (
        "Source/FitbitExtract/tests/bad_directory"
    )
    local_token_manager.parameters.make_directory = False

    with pytest.raises(
        FileNotFoundError, match="\\[Errno 2\\] No such file or directory:.*"
    ):
        local_token_manager.save_token(api_token)


def test_load_local_token(local_token_manager, api_token) -> None:
    """
    Test the load local token function to ensure it returns expected result
    """
    local_token_manager.save_token(api_token)

    credentials = local_token_manager.load_token()

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
    Test the get_access_token function to check that it returns
     a response for when http status is not OK
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
    Test the get_access_token function to check that it
    returns a response for when http status is not OK
    """
    parameters = auth.LocalTokenManagerParameters(load_credentials=False)
    bad_local_token_mabager = auth.LocalTokenManager(parameters=parameters)

    with pytest.raises(AttributeError, match="credentials attribute has not been set"):
        bad_local_token_mabager.refresh_token(api_token)


############################################
# Perform Tests on CloudTokenManager Class #
############################################

# def test_local_token_manager_default_init():
#     local_token_manager = auth.LocalTokenManager()
#     assert local_token_manager.parameters == auth.LocalTokenManagerParameters()
