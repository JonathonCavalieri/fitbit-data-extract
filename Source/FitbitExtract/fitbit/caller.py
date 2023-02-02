from datetime import datetime
from http import HTTPStatus

from dataclasses import dataclass, field
from fitbit.authorization import FitbitToken, TokenManager
from fitbit.constants import WEB_API_URL
from fitbit.savers import FitbitResponseSaver
from fitbit.requesters import FitbitRequester


@dataclass
class EndpointParameters:
    name: str
    method: str = "GET"
    response_format: str = "json"
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
        self.registered_endpoints = []
        self.available_endpoints = {
            "get_heart_rate_by_date": self.create_url_heart_rate,
            "get_body_weight_by_date": self.create_url_body_weight,
            "get_activity_summary_by_date": self.create_url_activity_summary,
            "get_activity_tcx_by_id": self.create_url_activity_tcx,
            "get_activity_details_by_id": self.create_url_activity_details,
            "get_heart_rate_variablity_by_date": self.create_url_heart_rate_variablity,
            "get_cardio_score_by_date": self.create_url_cardio_score,
            "get_sleep_by_date": self.create_url_sleep,
        }

    def refresh_access_token(self) -> None:
        """
        Refreshes the access token and saves back to source location
        """
        self.user_token = self.token_manager.refresh_token(self.user_token)
        self.token_manager.save_token(self.user_token)

    def register_multiple_endpoints(self, endpoints: list[EndpointParameters]) -> None:
        """
        Registers multiple endpoints from dictionary object

        Args:
            endpoints (dict): Of endpoints should be format {endpoint_name : endpoint_parameters}
        """

        for endpoint in endpoints:
            self.register_endpoint(endpoint)

    def register_endpoint(self, endpoint: EndpointParameters) -> None:
        """Register an endpoint to be called along with the parameters needed for calling if any

        Args:
            endpoint (str): Name of endpoint from the avaliable endpoint list
            parameters (dict): parameters used when calling the api

        Raises:
            ValueError: If the selected endpoint is not in the available list
        """
        if endpoint.name not in self.available_endpoints:
            raise ValueError(f"{endpoint.name} not in avaliable list")

        self.registered_endpoints.append(endpoint)

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
        for endpoint in self.registered_endpoints:
            # setup url
            url_func = self.available_endpoints[endpoint.name]
            url_kwargs = endpoint.url_kwargs
            url, instance_name = url_func(date, **url_kwargs)
            # setup headers
            headers = {"authorization": self.user_token.return_authorization()}
            headers = {**headers, **endpoint.headers}
            # setup body
            body = {**endpoint.body}
            # Setup save parameters
            folder = f"{endpoint.name}/{data_str}"
            file_name = f"{instance_name}_{self.user_token.user_id}"

            for attempt_number in range(1, retries + 2):

                data, httpcode = self.requester.make_request(
                    endpoint.method, url, headers, body
                )

                if httpcode == HTTPStatus.UNAUTHORIZED:
                    self.refresh_access_token()

                if httpcode == HTTPStatus.FORBIDDEN:
                    raise Exception("Request is forbidden please check user scope")

                if httpcode == HTTPStatus.OK:
                    self.response_saver.save(
                        data, folder, file_name, endpoint.response_format
                    )
                    break
                if attempt_number == retries + 1:
                    raise Exception(f"Request failed after {retries} retries")

    # Methods to generate the fitbit URLs for each endpoint
    def create_url_heart_rate(
        self, date: datetime.date, period: str = "1d"
    ) -> tuple[str, str]:
        """Generates the URL for calling the heart rate endpoint

        Args:
            date (date): The date in the format yyyy-MM-dd or today
            period (str, optional): Number of data points to include. Defaults to "1d".

        Raises:
            ValueError: errors if period is not in supported list

        Returns:
            str: Get request URL to call to retrieve the data
            str: Instance file name for saving
        """
        if period not in ["1d", "7d", "30d", "1w", "1m"]:
            raise ValueError("Period is not one of the supported values")

        return (
            f"{WEB_API_URL}/1/user/{self.user_token.user_id}/activities/heart/date/{date}/{period}.json",
            "get_heart_rate_by_date",
        )

    def create_url_body_weight(self, date: datetime.date) -> tuple[str, str]:
        """Generates the URL for calling the body weight endpoint

        Args:
            user_token (FitbitToken): users api token object
            date (date): The date in the format yyyy-MM-dd or today

        Returns:
            str: Get request URL to call to retrieve the data
            str: Instance file name for saving
        """

        return (
            f"{WEB_API_URL}/1/user/{self.user_token.user_id}/body/log/weight/date/{date}.json",
            "get_body_weight_by_date",
        )

    def create_url_activity_summary(self, date: datetime.date) -> tuple[str, str]:
        """Generates the URL for calling the activity summary endpoint

        Args:
            user_token (FitbitToken): users api token object
            date (date): The date in the format yyyy-MM-dd or today

        Returns:
            str: Get request URL to call to retrieve the data
            str: Instance file name for saving
        """
        return (
            f"{WEB_API_URL}/1/user/{self.user_token.user_id}/activities/date/{date}.json",
            "get_activity_summary_by_date",
        )

    def create_url_activity_tcx(
        self, date: datetime.date, log_id: str = None, partialtcx: bool = True
    ) -> tuple[str, str]:

        if log_id is None:
            raise ValueError("log_id was not provided as a parameter")

        if partialtcx:
            partialtcx_str = "true"
        else:
            partialtcx_str = "false"

        return (
            f"{WEB_API_URL}/1/user/{self.user_token.user_id}/activities/{log_id}.tcx?includePartialTCX={partialtcx_str}",
            f"{log_id}_get_activity_tcx_by_id",
        )

    def create_url_activity_details(
        self, date: datetime.date, log_id: str = None
    ) -> tuple[str, str]:

        if log_id is None:
            raise ValueError("log_id was not provided as a parameter")

        return (
            f"{WEB_API_URL}/1/user/{self.user_token.user_id}/activities/{log_id}.json",
            f"{log_id}_get_activity_details_by_id",
        )

    def create_url_heart_rate_variablity(self, date: datetime.date) -> tuple[str, str]:

        return (
            f"{WEB_API_URL}/1/user/{self.user_token.user_id}/hrv/date/{date}/all.json",
            "get_heart_rate_variablity_by_date",
        )

    def create_url_cardio_score(self, date: datetime.date) -> tuple[str, str]:

        return (
            f"{WEB_API_URL}/1/user/{self.user_token.user_id}/cardioscore/date/{date}.json",
            "get_cardio_score_by_date",
        )

    def create_url_sleep(self, date: datetime.date) -> tuple[str, str]:

        return (
            f"{WEB_API_URL}/1.2/user/{self.user_token.user_id}/sleep/date/{date}.json",
            "get_sleep_by_date",
        )
