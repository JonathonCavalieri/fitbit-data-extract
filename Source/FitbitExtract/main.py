from datetime import datetime, timedelta, date
import base64
import ast

import functions_framework

from fitbit.authorization import CloudTokenManager  # , LocalTokenManager
from fitbit.requesters import WebAPIRequester
from fitbit.savers import GCPResponseSaver  # , LocalResponseSaver
from fitbit.caller import FitBitCaller, EndpointParameters


ENDPOINTS = [
    EndpointParameters("get_heart_rate_by_date"),
    EndpointParameters("get_body_weight_by_date"),
    EndpointParameters("get_activity_summary_by_date"),
]


def call_api(date: date, user_id: str, endpoints: list[EndpointParameters]) -> None:

    # token_manager = LocalTokenManager()
    token_manager = CloudTokenManager(PROJECT_ID, BUCKET_NAME, user_id)
    fitbit_requester = WebAPIRequester()
    response_saver = GCPResponseSaver(BUCKET_NAME, PROJECT_ID)
    # response_saver = LocalResponseSaver("local_data/data")
    user_token = token_manager.load_token()
    fit_bit_caller = FitBitCaller(
        user_token, response_saver, fitbit_requester, token_manager
    )
    fit_bit_caller.register_multiple_endpoints(endpoints)
    fit_bit_caller.refresh_access_token()
    fit_bit_caller.make_registered_requests_for_date(date)


def decode_event_messages(message_data) -> dict:
    pubsub_message = base64.b64decode(message_data["message"]["data"])
    try:
        pubsub_message_decoded = pubsub_message.decode("UTF-8")
        return ast.literal_eval(pubsub_message_decoded)
    except Exception as exc:
        print(exc)
        raise Exception(
            f"Could not parse pubsub message: {pubsub_message} into a dict"
        ) from exc


def check_parameters(parameters: dict) -> None:
    if "date" not in parameters:
        raise KeyError("date was not provided in message body")

    if "user_id" not in parameters:
        raise KeyError("user_id was not provided in message body")

    if "endpoints" not in parameters:
        raise KeyError("endpoints was not provided in message body")


def get_endpoints(run_parameters: dict) -> list[EndpointParameters]:
    if not type(run_parameters["endpoints"]) == list:
        raise ValueError("Endpoints should be passed as a list even for a single value")

    if run_parameters["endpoints"] == ["all"]:
        endpoints_list = ENDPOINTS
    else:
        endpoints_list = []
        for endpoint in run_parameters["endpoints"]:
            endpoint_name = endpoint["name"]
            endpoint_kwargs = {}

            if "method" in endpoint:
                endpoint_kwargs["method"] = endpoint["method"]

            if "response_format" in endpoint:
                endpoint_kwargs["response_format"] = endpoint["response_format"]

            if "url_kwargs" in endpoint:
                endpoint_kwargs["url_kwargs"] = endpoint["url_kwargs"]

            if "headers" in endpoint:
                endpoint_kwargs["headers"] = endpoint["headers"]

            if "body" in endpoint:
                endpoint_kwargs["body"] = endpoint["body"]

            endpoint = EndpointParameters(endpoint_name, **endpoint_kwargs)
            endpoints_list.append(endpoint)

    return endpoints_list


def get_date(run_parameters: dict) -> date:
    if run_parameters["date"] == "current":
        return_date = date.today() - timedelta(days=1)
    else:
        return_date = datetime.strptime(run_parameters["date"], "%Y-%m-%d").date()

    return return_date


@functions_framework.cloud_event
def main(cloud_event) -> None:
    run_parameters = decode_event_messages(cloud_event.data)
    check_parameters(run_parameters)

    user_id = run_parameters["user_id"]
    date = get_date(run_parameters)
    endpoints = get_endpoints(run_parameters)

    call_api(date, user_id, endpoints)


if __name__ == "__main__":
    pass
