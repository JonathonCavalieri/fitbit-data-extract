from typing import Protocol
import requests


class FitbitRequester(Protocol):
    """
    Interface protocol for a Fitbit Requester. These classes will be used to get the
     data from fitbit API

    Methods
    make_request(str, dict, dict) -> None: Save the response to the target location
    """

    def make_request(
        self, method: str, url: str, headers: dict, body: dict
    ) -> tuple[str, int]:
        """Save the response to the target location"""


class WebAPIRequester:
    def make_request(  # pylint: disable=W0613
        self, method: str, url: str, headers: dict, body: dict
    ) -> tuple[str, int]:

        if method == "GET":
            return self._make_get_request(url, headers)

        raise ValueError("Invalid method")

    def _make_get_request(self, url: str, headers: dict) -> tuple[str, int]:
        response = requests.get(url, headers=headers, timeout=600)
        return response.text, response.status_code
