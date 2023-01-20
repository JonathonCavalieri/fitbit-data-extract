from datetime import datetime

from fitbit.authorization import LocalTokenManager
from fitbit.requesters import WebAPIRequester
from fitbit.savers import GCPResponseSaver
from fitbit.caller import FitBitCaller, EndpointParameters


# def test() -> None:
#     user_token = auth.load_local_token()
#     print(user_token)
#     app_credentials = auth.load_local_credentials()
#     print(app_credentials)
#     token_new = auth.refresh_access_token(user_token, app_credentials)
#     print(token_new)
#     auth.save_local_token(token_new)
ENDPOINTS = {
    "get_heart_rate_by_date": EndpointParameters("GET", "json"),
    "get_body_weight_by_date": EndpointParameters("GET", "json"),
}

PROJECT_ID = "fitbit-data-extract"
BUCKET_NAME = "fitbit-data-extract-prod"


def main(date: datetime) -> None:

    token_manager = LocalTokenManager(
        credentials_parameters={"name": "credentials"}, load_credentials=True
    )
    fitbit_requester = WebAPIRequester()
    response_saver = GCPResponseSaver(BUCKET_NAME, PROJECT_ID)
    user_token = token_manager.load_token()
    fit_bit_caller = FitBitCaller(
        user_token, response_saver, fitbit_requester, token_manager
    )
    fit_bit_caller.register_multiple_endpoints(ENDPOINTS)
    print(fit_bit_caller.user_token.refresh_token)
    fit_bit_caller.refresh_access_token()
    fit_bit_caller.make_registered_requests_for_date(date)


if __name__ == "__main__":
    date = datetime.strptime("2023-01-17", "%Y-%m-%d").date()
    main(date)
