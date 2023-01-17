from datetime import datetime
import os
from http import HTTPStatus
from typing import Protocol

from fitbit.authorization import FitbitToken, TokenManager
from fitbit.constants import WEB_API_URL


class FitbitResponseSaver(Protocol):
    """
    Interface protocol for a Fitbit Response Saver. These classes will be used to save
    the different response to different locations

    Methods
    save(str, str, str, str) -> None: Save the response to the target location
    """

    def save(
        self, response: str, folder: str, file_name: str, file_format: str
    ) -> None:
        """Save the response to the target location"""


class FitbitRequester(Protocol):
    """
    Interface protocol for a Fitbit Requester. These classes will be used to get the
     data from fitbit API

    Methods
    make_request(str, dict, dict) -> None: Save the response to the target location
    """

    def make_request(
        self, url: str, headers: dict, body: dict
    ) -> tuple[str, HTTPStatus]:
        """Save the response to the target location"""


class FitBitCaller:
    """This object is used to call the various different fitbit APIs"""

    def __init__(
        self,
        user_token: FitbitToken,
        response_saver: FitbitResponseSaver,
        requester: FitbitRequester,
        token_manager: TokenManager,
    ) -> None:
        self.user_token = user_token
        self.response_saver = response_saver
        self.requester = requester
        self.token_manager = token_manager
        self.registered_endpoints = {}
        self.available_endpoints = {
            "get_heart_rate_by_date": self.create_url_heart_rate,
            "get_body_weight_by_date": self.create_url_body_weight,
        }

    def register_endpoint(self, endpoint: str, parameters: dict) -> None:
        """Register an endpoint to be called along with the parameters needed for calling if any

        Args:
            endpoint (str): Name of endpoint from the avaliable endpoint list
            parameters (dict): parameters used when calling the api

        Raises:
            ValueError: If the selected endpoint is not in the available list
        """
        if endpoint not in self.available_endpoints:
            raise ValueError(f"{endpoint} not in avaliable list")

        self.registered_endpoints[endpoint] = parameters

    # Methods to generate the fitbit URLs for each endpoint
    def create_url_heart_rate(
        self, user_token: FitbitToken, date: datetime.date, period: str = "1d"
    ) -> str:
        """Generates the URL for calling the heart rate endpoint

        Args:
            user_token (FitbitToken): users api token object
            date (date): The date in the format yyyy-MM-dd or today
            period (str, optional): Number of data points to include. Defaults to "1d".

        Raises:
            ValueError: errors if period is not in supported list

        Returns:
            str: Get request URL to call to retrieve the data
        """
        if period not in ["1d", "7d", "30d", "1w", "1m"]:
            raise ValueError("Period is not one of the supported values")

        return f"{WEB_API_URL}/user/{user_token.user_id}/activities/heart/date/{date}/{period}.json"

    def create_url_body_weight(
        self, user_token: FitbitToken, date: datetime.date
    ) -> str:
        """Generates the URL for calling the body weight endpoint

        Args:
            user_token (FitbitToken): users api token object
            date (date): The date in the format yyyy-MM-dd or today

        Returns:
            str: Get request URL to call to retrieve the data
        """

        return (
            f"{WEB_API_URL}/user/{user_token.user_id}/body/log/weight/date/{date}.json"
        )


class LocalResponseSaver:
    def __init__(self, base_location, make_directory=True) -> None:
        self.base_location = base_location
        self.make_directory = make_directory

    def save(
        self, response: str, folder: str, file_name: str, file_format: str
    ) -> None:
        directory = f"{self.base_location}/{folder}"
        full_path = f"{directory}/{file_name}.{file_format}"

        if not os.path.exists(directory) and self.make_directory:
            os.makedirs(directory)

        with open(full_path, "w", encoding="utf-8") as file:
            file.write(response)
