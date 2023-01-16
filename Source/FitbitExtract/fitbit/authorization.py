from json import load as json_load, dump as json_dump
import os
from dataclasses import dataclass, asdict
import requests

from fitbit.constants import TOKEN_URL


@dataclass
class FitbitToken:
    """Fitbit API Token Details"""

    refresh_token: str
    access_token: str
    scope: str
    user_id: str
    access_token_isvalid: bool = False

    def return_authorization(self) -> str:
        """returns the authorization header for a valid access token

        Raises:
            ValueError: raise if access token is invalid

        Returns:
            str: authorization header
        """
        if self.access_token_isvalid:
            return f"Bearer {self.access_token}"
        else:
            raise ValueError("Access token is invalid")


@dataclass
class FitbitAppCredentials:
    """FitBit App credentials"""

    client_id: str
    client_secret: str


def save_local_token(
    token: FitbitToken,
    directory: str = "local_data",
    name: str = "token",
    make_directory: bool = True,
) -> None:
    """Saves a Fitbit API token to the local drive
    Args:
        token (FitbitToken): Token to be saved
        directory (str, optional): Directory where to save the token. Defaults to "local_data".
        name (str, optional): Name of file. Defaults to "token".
        make_directory (bool, optional): Create the dirctory if it doesn't exist. Defaults to True.
    """
    if not os.path.exists(directory) and make_directory:
        os.makedirs(directory)

    full_path = f"{directory}/{name}.json"

    out_data = asdict(token)

    with open(full_path, "w", encoding="utf-8") as file:
        json_dump(out_data, file, ensure_ascii=False, indent=4)


def load_local_token(path: str = "local_data", name: str = "token") -> FitbitToken:
    """loads the local token. This is mostly used for testing on local machine

    Args:
        path (str, optional): path to folder containing the credentials file. Defaults to 'local_data'.
        name (str, optional): name of the token file. Defaults to 'token'.

    Returns:
        FitbitToken: FitbitToken object containing access and refresh token details
    """
    file_name = f"{path}/{name}.json"
    with open(file_name, "r", encoding="utf-8") as file:
        token_file = json_load(file)

    new_token = FitbitToken(
        token_file["refresh_token"],
        token_file["access_token"],
        token_file["scope"],
        token_file["user_id"],
    )
    return new_token


def load_local_credentials(
    path: str = "local_data", name: str = "credentials"
) -> FitbitAppCredentials:
    """loads the local credentials. This is mostly used for testing on local machine

    Args:
        path (str, optional): path to folder containing the credentials file. Defaults to 'local_data'.
        name (str, optional): name of the credentials file. Defaults to 'credentials'.

    Returns:
        FitbitAppCredentials: FitbitAppCredentials object containg client id and secret details
    """
    file_name = f"{path}/{name}.json"
    with open(file_name, "r", encoding="utf-8") as file:
        credentials_file = json_load(file)

    new_token = FitbitAppCredentials(
        credentials_file["client_id"], credentials_file["client_secret"]
    )
    return new_token


def refresh_access_token(
    token: FitbitToken, credential: FitbitAppCredentials
) -> FitbitToken:
    """_summary_

    Args:
        token (FitbitToken): Token object with access and refresh token that will be refreshed in api call
        credential (FitbitAppCredentials): the applications client id and secret in a credentials object

    Returns:
        FitbitToken: new token
    """
    body = {
        "grant_type": "refresh_token",
        "refresh_token": token.refresh_token,
        "client_id": credential.client_id,
    }
    headers = {"Content-type": "application/x-www-form-urlencoded"}
    response = requests.post(
        TOKEN_URL,
        headers=headers,
        data=body,
        timeout=600,
        auth=(credential.client_id, credential.client_secret),
    )

    response.raise_for_status()
    response_credentials = response.json()
    new_token = FitbitToken(
        response_credentials["refresh_token"],
        response_credentials["access_token"],
        response_credentials["scope"],
        response_credentials["user_id"],
        access_token_isvalid=True,
    )
    return new_token
