from datetime import datetime
from http import HTTPStatus
from typing import Protocol

from fitbit.authorization import FitbitToken
from fitbit.constants import WEB_API_URL


class FitbitResponseSaver(Protocol):
    def save(self) -> None:
        pass


class FitbitRequester(Protocol):
    def make_request(self, url: str, headers: dict) -> tuple(dict, HTTPStatus):
        pass


class fitbitcaller:
    def __init__(
        self,
        user_token: FitbitToken,
        response_saver: FitbitResponseSaver,
        requester: FitbitRequester,
    ) -> None:
        self.user_token = user_token
        self.response_saver = response_saver
        self.requester = requester
        self.registered_endpoints = {}
        self.available_endpoints = {
            "get_heart_rate_by_date": self.create_url_heart_rate,
            "get_body_weight_by_date": self.create_url_body_weight,
        }

    def register_endpoint(self, endpoint: str, parameters: dict) -> None:
        if endpoint not in self.available_endpoints.keys():
            raise ValueError(f"{endpoint} not in avaliable list")

        self.registered_endpoints[endpoint] = parameters

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
