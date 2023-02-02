import helper.functions as helper
from fitbit.transform import FitbitETL
from fitbit.loaders import LocalDataLoader
import helper.localfunctions as localhelper
from fitbit.caller import EndpointParameters
import re
from fitbit import constants as fit_constants
from fitbit.transform import flattern_dictionary
from fitbit.loaders import GCPDataLoader, LocalDataLoader
from fitbit.messenger import PubSubMessenger, LocalMessenger


PROJECT_ID = helper.get_config_parameter("config.json", "gcp_project")
BUCKET_NAME = helper.get_config_parameter("config.json", "gcp_bucket_file_store")
DATASET_NAME = helper.get_config_parameter("config.json", "gcp_bq_dataset")
TOPIC_NAME = helper.get_config_parameter("config.json", "pub_sub_topic_name")


def testing() -> None:
    # file_path = "local_data/data/get_heart_rate_by_date/20230117/get_heart_rate_by_date_8HQJ4D.json"
    file_path = "local_data/data/get_activity_summary_by_date/20230117/get_activity_summary_by_date_8HQJ4D.json"
    # file_path = "local_data/data/get_body_weight_by_date/20230117/get_body_weight_by_date_8HQJ4D.json"
    # file_path = "local_data/data/get_activity_tcx_by_id/20230130/51468247593_get_activity_tcx_by_id_8HQJ4D.tcx"
    # file_path = "local_data/data/get_cardio_score_by_date/20230118/get_cardio_score_by_date_8HQJ4D.json"
    # file_path = (
    #     "local_data/data/get_sleep_by_date/20230118/get_sleep_by_date_8HQJ4D.json"
    # )

    parser = FitbitETL(LocalDataLoader(), LocalMessenger())
    # parser.get_details_from_path(file_path)

    # # data = local_data_loader.load(file_path)
    parser.process(file_path)
    print(parser.instance_id, parser.user_id, parser.endpoint)


def testing2() -> None:
    user_id = "8HQJ4D"
    localhelper.call_api_local("2022-10-13", user_id, PROJECT_ID, BUCKET_NAME)
    localhelper.call_api_local("2023-01-15", user_id, PROJECT_ID, BUCKET_NAME)
    localhelper.call_api_local("2023-01-16", user_id, PROJECT_ID, BUCKET_NAME)
    localhelper.call_api_local("2023-01-17", user_id, PROJECT_ID, BUCKET_NAME)
    localhelper.call_api_local("2023-01-18", user_id, PROJECT_ID, BUCKET_NAME)


def testing3() -> None:
    user_id = "8HQJ4D"

    log_ids = [
        53177087392,
        53409181820,
        53405172385,
        51489022277,
        51468247593,
        51413848113,
        53177087392,
    ]
    endspoints = []
    for id in log_ids:
        parameters_tcx = EndpointParameters(
            "get_activity_tcx_by_id",
            response_format="tcx",
            url_kwargs={"log_id": f"{id}"},
        )
        endspoints.append(parameters_tcx)
    localhelper.call_api_local(
        "2023-01-30",
        user_id,
        PROJECT_ID,
        BUCKET_NAME,
        endpoints=endspoints,
    )


def testing4() -> None:
    test_dict = {
        "test1": "value1",
        "test2": {"nested1": "nested_value1"},
        "test3": {"nested2": "nested_value2"},
        "test4": {
            "nested3": "nested_value3",
            "nested4": {"secondnested1": "secondnested_value1"},
        },
    }

    print(flattern_dictionary(test_dict))


def testing_gcp_loader():
    data_loader = GCPDataLoader(PROJECT_ID, BUCKET_NAME, DATASET_NAME)
    parser = FitbitETL(data_loader, LocalMessenger())
    # file = data_loader.extract("test_folder/test.json")
    # print(type(file), file)
    file_path = (
        "get_activity_summary_by_date/20230117/get_activity_summary_by_date_8HQJ4D.json"
    )

    parser.process(file_path)


def testing_pubsub_messenger():
    messenger = PubSubMessenger(PROJECT_ID, "fitbit-testing-topic")
    user_id = "test_user"
    date = "2023-01-01"
    endpoints = [
        EndpointParameters(
            name="get_activity_tcx",
            method="GET",
            response_format="tcx",
            url_kwargs={"log_id": 53198490566},
            body={},
            headers={},
        ),
        EndpointParameters(
            name="get_activity_tcx",
            method="GET",
            response_format="tcx",
            url_kwargs={"log_id": 53198490567},
            body={},
            headers={},
        ),
        EndpointParameters(
            name="get_activity_tcx",
            method="GET",
            response_format="tcx",
            url_kwargs={"log_id": 53198490568},
            body={},
            headers={},
        ),
    ]

    message_publish = messenger.prep_message(endpoints, user_id, date)
    future = type(messenger.send_message(message_publish))
    print(future)


def testing_main_transform_load(cloud_event) -> None:
    data = cloud_event.data
    file_bucket = data["bucket"]
    file_name = data["name"]
    helper.transform_load(
        PROJECT_ID,
        file_bucket,
        file_name,
        TOPIC_NAME,
        DATASET_NAME,
    )


class FakeEvent:
    def __init__(self) -> None:
        self.data = {
            "bucket": "fitbit-data-extract-prod",
            "name": "get_activity_summary_by_date/20230117/get_activity_summary_by_date_8HQJ4D.json",
        }


def testing_debug():
    loader = GCPDataLoader(PROJECT_ID, BUCKET_NAME, DATASET_NAME)
    transformer1 = FitbitETL(LocalDataLoader(), LocalMessenger())
    transformer2 = FitbitETL(loader, LocalMessenger())
    file = "local_data/data/get_activity_tcx_by_id/20230130/53177087392_get_activity_tcx_by_id_8HQJ4D.tcx"
    file2 = (
        "get_activity_tcx_by_id/20230118/53177087392_get_activity_tcx_by_id_8HQJ4D.tcx"
    )

    # transformer1.process(file)
    transformer2.process(file2)


if __name__ == "__main__":
    # fake_event = FakeEvent()
    # testing_main_transform_load(fake_event)
    # testing_pubsub_messenger()
    testing_debug()
