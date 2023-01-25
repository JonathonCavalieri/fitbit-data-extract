import json
import os
from typing import Protocol
from dataclasses import dataclass, asdict

import requests
from cryptography.fernet import Fernet
from google.cloud import secretmanager, storage

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

    def load_credentials(self) -> None:
        """Load Credentials from storage"""

    def load_token(self) -> FitbitToken:
        """Load API Token from storage"""

    def save_token(self, token: FitbitToken) -> None:
        """Save API Token to storage"""


@dataclass
class LocalTokenManagerParameters:
    credentials_directory: str = "local_data"
    credentials_name: str = "credentials"
    token_directory: str = "local_data"
    token_name: str = "token"
    make_directory: bool = True
    load_credentials: bool = True


class LocalTokenManager:
    """A token manager to be used when testing the fitbit api locally"""

    def __init__(
        self,
        parameters: LocalTokenManagerParameters = None,
        credentials: FitbitAppCredentials = None,
    ) -> None:
        """Intialise the local token manager

        Args:
            parameters (LocalTokenManagerParameters, optional): Parameters for the local token manager. Defaults to LocalTokenManagerParameters.
            credentials (FitbitAppCredentials, optional): App credentials. Defaults to None.
        """
        # Instantiate class variables
        if parameters is None:
            self.parameters = LocalTokenManagerParameters()
        else:
            self.parameters = parameters
        self.credentials = credentials

        # Perform class setup
        if self.parameters.load_credentials:
            self.load_credentials()

    def load_credentials(self) -> None:
        """
        Load app credentials from local storage into the local token manger object
        """
        directory = self.parameters.credentials_directory
        name = self.parameters.credentials_name
        file_name = f"{directory}/{name}.json"
        with open(file_name, "r", encoding="utf-8") as file:
            credentials_file = json.load(file)

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

    def load_token(self) -> FitbitToken:
        """
        Loads the local token. This is mostly used for testing on local machine

        Returns:
            FitbitToken: FitbitToken object containing access and refresh token details
        """
        directory = self.parameters.token_directory
        name = self.parameters.token_name
        file_name = f"{directory}/{name}.json"
        with open(file_name, "r", encoding="utf-8") as file:
            token_file = json.load(file)

        new_token = FitbitToken(
            token_file["refresh_token"],
            token_file["access_token"],
            token_file["scope"],
            token_file["user_id"],
        )
        return new_token

    def save_token(self, token: FitbitToken) -> None:
        """
        Saves a Fitbit API token to the local drive
        """
        directory = self.parameters.token_directory
        name = self.parameters.token_name
        if not os.path.exists(directory) and self.parameters.make_directory:
            os.makedirs(directory)

        full_path = f"{directory}/{name}.json"

        out_data = asdict(token)

        with open(full_path, "w", encoding="utf-8") as file:
            json.dump(out_data, file, ensure_ascii=False, indent=4)


@dataclass
class CloudTokenManagerParameters:
    encryption_key_name: str = "fitbitapp_encryption_key"
    client_id_name: str = "fitbitapp_client_id"
    client_secret_name: str = "fitbitapp_client_secret"
    token_folder: str = "user_tokens"


class CloudTokenManager:
    """
    Interface protocol for a Token Manager

    Methods
    refresh_token(FitbitToken) -> FitbitToken: Refreshes a fitbit access token
    load_credentials(dict) -> None: Load Credentials from storage
    load_token(dict) -> FitbitToken: Load API Token from storage
    save_token(FitbitToken, dict) -> None: Load API Token from storage
    """

    def __init__(
        self,
        project_id: str,
        bucket_name: str,
        user_id: str,
        parameters: CloudTokenManagerParameters = None,
    ) -> None:

        if parameters is None:
            self.parameters = CloudTokenManagerParameters()
        else:
            self.parameters = parameters
        self.user_id = user_id
        self.project_id = project_id
        self.storage_client = storage.Client(project=project_id)
        self.bucket = self.storage_client.get_bucket(bucket_name)
        self.secret_client = secretmanager.SecretManagerServiceClient()

        self.encryption_key = self.load_encryption_key()
        self.credentials = self.load_credentials()

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

    def _load_secret_from_gcp(self, secret_name: str) -> str:
        """Loads a secrey from GCP secret manager for a given secret name

        Args:
            secret_name (str): Name of the secret

        Returns:
            str: secret value
        """
        resource_name = (
            f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
        )
        response = self.secret_client.access_secret_version(
            request={"name": resource_name}
        )
        return response.payload.data  # .decode("UTF-8")

    def load_encryption_key(self) -> str:
        """Gets the encryption key stored in the GCP secret manager

        Returns:
            str: The encryption key used to decrypt other credentials
        """
        key = self._load_secret_from_gcp(self.parameters.encryption_key_name)
        return Fernet(key)

    def load_credentials(self) -> None:
        """Load Credentials from google cloud platform secret manager"""

        client_id = self._load_secret_from_gcp(self.parameters.client_id_name)
        client_secret = self._load_secret_from_gcp(self.parameters.client_secret_name)
        return FitbitAppCredentials(client_id, client_secret)

    def load_token(self) -> FitbitToken:
        """Load API Token from storage"""
        blob_name = f"{self.parameters.token_folder}/{self.user_id}_token_encrypted"
        blob = self.bucket.get_blob(blob_name)
        token_file = blob.download_as_string()
        token_file = self.encryption_key.decrypt(token_file)
        token_file = json.loads(token_file)

        new_token = FitbitToken(
            token_file["refresh_token"],
            token_file["access_token"],
            token_file["scope"],
            token_file["user_id"],
        )
        return new_token

    def save_token(self, token: FitbitToken) -> None:
        """Save API Token to storage"""

        out_data = asdict(token)
        out_data = json.dumps(out_data).encode("utf-8")
        out_data = self.encryption_key.encrypt(out_data)

        blob_name = f"{self.parameters.token_folder}/{self.user_id}_token_encrypted"

        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(out_data)
