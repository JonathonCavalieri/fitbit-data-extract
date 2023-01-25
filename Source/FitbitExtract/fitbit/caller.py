from datetime import datetime
from http import HTTPStatus

from dataclasses import dataclass, field
from fitbit.authorization import FitbitToken, TokenManager
from fitbit.constants import WEB_API_URL
from fitbit.savers import FitbitResponseSaver
from fitbit.requesters import FitbitRequester


@dataclass
class EndpointParameters:
    method: str
    response_format: str
    url_kwargs: dict = field(default_factory=dict)
    body: dict = field(default_factory=dict)
    headers: dict = field(default_factory=dict)


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
            "get_activity_summary_by_date": self.create_url_activity_summary,
        }

    def refresh_access_token(self) -> None:
        """
        Refreshes the access token and saves back to source location
        """
        self.user_token = self.token_manager.refresh_token(self.user_token)
        self.token_manager.save_token(self.user_token)

    def register_multiple_endpoints(self, endpoints: dict) -> None:
        """
        Registers multiple endpoints from dictionary object

        Args:
            endpoints (dict): Of endpoints should be format {endpoint_name : endpoint_parameters}
        """

        for endpoint, parameter in endpoints.items():
            self.register_endpoint(endpoint, parameter)

    def register_endpoint(self, endpoint: str, parameters: EndpointParameters) -> None:
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

    def make_registered_requests_for_date(self, date: datetime.date, retries: int = 5):
        """Makes all the requests for the APIs that have been registered.

        Args:
            date (datetime.date): Date to run the API calls for
            retries (int, optional): _description_. Defaults to 5.

        Raises:
            Exception: If no endpoints have been registered
            ValueError: If retries are negative
            Exception: If calling the endpoint does not work after the specified number of retries
        """
        data_str = date.strftime("%Y%m%d")

        if len(self.registered_endpoints) < 1:
            raise Exception("No endpoints have been registered")

        if retries < 0:
            raise ValueError("Retries cannot be less than 0")

        if not self.user_token.access_token_isvalid:
            self.refresh_access_token()
        for endpoint, parameters in self.registered_endpoints.items():
            # setup url
            url_func = self.available_endpoints[endpoint]
            url_kwargs = parameters.url_kwargs
            url = url_func(date, **url_kwargs)
            # setup headers
            headers = {"authorization": self.user_token.return_authorization()}
            headers = {**headers, **parameters.headers}
            # setup body
            body = {**parameters.body}
            # Setup save parameters
            folder = f"{endpoint}/{data_str}"
            file_name = f"{endpoint}_{self.user_token.user_id}"

            for attempt_number in range(1, retries + 2):

                data, httpcode = self.requester.make_request(
                    parameters.method, url, headers, body
                )

                if httpcode == HTTPStatus.UNAUTHORIZED:
                    self.refresh_access_token()

                if httpcode == HTTPStatus.OK:
                    self.response_saver.save(
                        data, folder, file_name, parameters.response_format
                    )
                    break
                if attempt_number == retries + 1:
                    raise Exception(f"Request failed after {retries} retries")

    # Methods to generate the fitbit URLs for each endpoint
    def create_url_heart_rate(self, date: datetime.date, period: str = "1d") -> str:
        """Generates the URL for calling the heart rate endpoint

        Args:
            date (date): The date in the format yyyy-MM-dd or today
            period (str, optional): Number of data points to include. Defaults to "1d".

        Raises:
            ValueError: errors if period is not in supported list

        Returns:
            str: Get request URL to call to retrieve the data
        """
        if period not in ["1d", "7d", "30d", "1w", "1m"]:
            raise ValueError("Period is not one of the supported values")

        return f"{WEB_API_URL}/user/{self.user_token.user_id}/activities/heart/date/{date}/{period}.json"

    def create_url_body_weight(self, date: datetime.date) -> str:
        """Generates the URL for calling the body weight endpoint

        Args:
            user_token (FitbitToken): users api token object
            date (date): The date in the format yyyy-MM-dd or today

        Returns:
            str: Get request URL to call to retrieve the data
        """

        return f"{WEB_API_URL}/user/{self.user_token.user_id}/body/log/weight/date/{date}.json"

    def create_url_activity_summary(self, date: datetime.date) -> str:
        """Generates the URL for calling the activity summary endpoint

        Args:
            user_token (FitbitToken): users api token object
            date (date): The date in the format yyyy-MM-dd or today

        Returns:
            str: Get request URL to call to retrieve the data
        """
        return (
            f"{WEB_API_URL}/user/{self.user_token.user_id}/activities/date/{date}.json"
        )
