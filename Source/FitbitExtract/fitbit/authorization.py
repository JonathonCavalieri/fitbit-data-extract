from json import load as json_load, dump as json_dump
import os
from typing import Protocol
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


class TokenManager(Protocol):
    """
    Interface protocol for a Token Manager

    Methods
    refresh_token(FitbitToken) -> FitbitToken: Refreshes a fitbit access token
    load_credentials(dict) -> None: Load Credentials from storage
    load_token(dict) -> FitbitToken: Load API Token from storage
    save_token(FitbitToken, dict) -> None: Load API Token from storage
    """

    def refresh_token(self, token: FitbitToken) -> FitbitToken:
        """Refreshes a fitbit access token"""

    def load_credentials(self, parameters: dict) -> None:
        """Load Credentials from storage"""

    def load_token(self, parameters: dict) -> FitbitToken:
        """Load API Token from storage"""

    def save_token(self, token: FitbitToken, parameters: dict = None) -> None:
        """Save API Token to storage"""


class LocalTokenManager:
    """A token manager to be used when testing the fitbit api locally"""

    def __init__(
        self,
        credentials_parameters: dict = None,
        token_parameters: dict = None,
        credentials: FitbitAppCredentials = None,
        load_credentials: bool = False,
    ) -> None:
        """Intialise the local token manager

        Args:
            credentials_parameters (dict, optional): parameter option to be passed onto the credentials methods. Defaults to None.
            token_parameters (dict, optional): parameter option to be passed onto the token methods. Defaults to None.
            credentials (FitbitAppCredentials, optional): Credentials object to be used by the token manager. Defaults to None.
            load_credentials (bool, optional): Should the token manager try to load a credentials object from local storage. Defaults to False.
        """
        # Instantiate class variables
        self.credentials_parameters = credentials_parameters
        self.token_parameters = token_parameters
        self.credentials = credentials

        # Perform class setup
        if load_credentials:
            self.load_credentials(parameters=credentials_parameters)

    def __return_path_parameters(
        self, parameters: dict = None
    ) -> tuple[str, str, bool]:
        """extracts the directory and name parameter from the parameters dictionary

        Args:
            parameters (dict): Dictionary of parameters

        Returns:
            tuple[str,str,bool]: directory, name
                directory: directory parameter. Defaults to 'local_data' if not in dictionary
                name: name of file parameter . Defaults to 'name' if not in dictionary
                make_directory: should it make make directory for saving. Defaults to 'True' if not in dictionary
        """
        if parameters is None:
            parameters = {}

        if "directory" not in parameters:
            directory = "local_data"
        else:
            directory = parameters["directory"]

        if "name" not in parameters:
            name = "token"
        else:
            name = parameters["name"]

        if "make_directory" not in parameters:
            make_directory = True
        else:
            make_directory = parameters["make_directory"]

        return directory, name, make_directory

    def load_credentials(self, parameters: dict = None) -> None:
        """Load app credentials from local storage into the local token manger object

        Args:
            parameters (dict): Dictionary of parameters

        Relavant parameters:
            directory str: directory to load credentials from. Defaults to 'local_data'
            name str: name of file. Defaults to 'token'
        """
        directory, name, _ = self.__return_path_parameters(parameters)
        file_name = f"{directory}/{name}.json"
        with open(file_name, "r", encoding="utf-8") as file:
            credentials_file = json_load(file)

        credentials = FitbitAppCredentials(
            credentials_file["client_id"], credentials_file["client_secret"]
        )
        self.credentials = credentials

    def refresh_token(self, token: FitbitToken) -> FitbitToken:
        """Refreshes the access token by calling the authorization endpoint with refresh token

        Args:
            token (FitbitToken): Token object with access and refresh token that will be refreshed in api call

        Returns:
            FitbitToken: new token
        """
        if self.credentials is None:
            raise AttributeError("credentials attribute has not been set")

        body = {
            "grant_type": "refresh_token",
            "refresh_token": token.refresh_token,
            "client_id": self.credentials.client_id,
        }
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        response = requests.post(
            TOKEN_URL,
            headers=headers,
            data=body,
            timeout=600,
            auth=(self.credentials.client_id, self.credentials.client_secret),
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

    def load_token(self, parameters: dict = None) -> FitbitToken:
        """
        Loads the local token. This is mostly used for testing on local machine
        Args:
            parameters (dict): Dictionary of parameters

        Relavant parameters:
            directory str: directory to load credentials from. Defaults to 'local_data'
            name str: name of file. Defaults to 'token'

        Returns:
            FitbitToken: FitbitToken object containing access and refresh token details
        """
        directory, name, _ = self.__return_path_parameters(parameters)
        file_name = f"{directory}/{name}.json"
        with open(file_name, "r", encoding="utf-8") as file:
            token_file = json_load(file)

        new_token = FitbitToken(
            token_file["refresh_token"],
            token_file["access_token"],
            token_file["scope"],
            token_file["user_id"],
        )
        return new_token

    def save_token(self, token: FitbitToken, parameters: dict = None) -> None:
        """Saves a Fitbit API token to the local drive
        Args:
            parameters (dict): Dictionary of parameters

        Relavant parameters:
            directory str: directory to load credentials from. Defaults to 'local_data'
            name str: name of file. Defaults to 'token'
            make_directory bool:
        """
        directory, name, make_directory = self.__return_path_parameters(parameters)
        if not os.path.exists(directory) and make_directory:
            os.makedirs(directory)

        full_path = f"{directory}/{name}.json"

        out_data = asdict(token)

        with open(full_path, "w", encoding="utf-8") as file:
            json_dump(out_data, file, ensure_ascii=False, indent=4)
