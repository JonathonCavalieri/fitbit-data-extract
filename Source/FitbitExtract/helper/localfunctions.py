from datetime import date, datetime


from fitbit.authorization import LocalTokenManager, CloudTokenManager
from fitbit.requesters import WebAPIRequester
from fitbit.savers import LocalResponseSaver
from fitbit.caller import FitBitCaller, EndpointParameters
from helper import constants


def call_api_local(
    date: str,
    user_id: str,
    project_id: str,
    bucket_name: str,
    endpoints: list[EndpointParameters] = None,
) -> None:

    date = datetime.strptime(date, "%Y-%m-%d").date()

    if endpoints is None:
        endpoints = constants.ENDPOINTS

    # token_manager = CloudTokenManager(project_id, bucket_name, user_id)
    token_manager = LocalTokenManager()
    token_manager.load_credentials()

    fitbit_requester = WebAPIRequester()

    response_saver = LocalResponseSaver("local_data/data")
    user_token = token_manager.load_token()
    fit_bit_caller = FitBitCaller(
        user_token, response_saver, fitbit_requester, token_manager
    )
    fit_bit_caller.register_multiple_endpoints(endpoints)
    fit_bit_caller.refresh_access_token()
    fit_bit_caller.make_registered_requests_for_date(date)
