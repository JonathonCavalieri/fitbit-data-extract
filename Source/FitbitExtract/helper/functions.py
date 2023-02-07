from datetime import datetime, timedelta, date
import base64
import ast
import os
import json


from fitbit.authorization import CloudTokenManager
from fitbit.requesters import WebAPIRequester
from fitbit.savers import GCPResponseSaver
from fitbit.caller import FitBitCaller, EndpointParameters
from fitbit.messengers import PubSubMessenger
from fitbit.transformers import FitbitETL
from fitbit.loaders import GCPDataLoader
from helper.constants import ENDPOINTS


def call_api(
    date: date,
    user_id: str,
    endpoints: list[EndpointParameters],
    project_id: str,
    bucket_name_cred: str,
    bucket_name_file: str,
) -> None:  # pragma: no cover

    token_manager = CloudTokenManager(project_id, bucket_name_cred, user_id)
    fitbit_requester = WebAPIRequester()
    response_saver = GCPResponseSaver(bucket_name_file, project_id)
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


def get_config_parameter(config_directory: str, parameter_name: str) -> str:
    if not os.path.exists(config_directory):
        raise Exception(f"No config file found at {config_directory}")

    with open(config_directory, "r", encoding="utf-8") as config_file:
        config_dictionary = json.load(config_file)

    if parameter_name not in config_dictionary:
        raise KeyError(f"Please add to {parameter_name}")

    if (
        config_dictionary[parameter_name] == ""
        or config_dictionary[parameter_name] is None
        or config_dictionary[parameter_name] == parameter_name
    ):
        raise ValueError(f"Please fill in {parameter_name} with a value")

    return config_dictionary[parameter_name]


def transform_load(
    project_id: str,
    file_bucket: str,
    file_name: str,
    topic_name: str,
    dataset_name: str,
) -> None:  # pragma: no cover
    messenger = PubSubMessenger(project_id, topic_name)
    loader = GCPDataLoader(project_id, file_bucket, dataset_name)
    transformer = FitbitETL(loader, messenger, file_bucket)

    transformer.process(file_name)
