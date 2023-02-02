import functions_framework
import helper.functions as helper

CONFIG = "config.json"
PROJECT_ID = helper.get_config_parameter(CONFIG, "gcp_project")
BUCKET_NAME_CREDENTIALS = helper.get_config_parameter(CONFIG, "gcp_bucket_credentials")
BUCKET_NAME_FILE_STORE = helper.get_config_parameter(CONFIG, "gcp_bucket_file_store")
DATASET_NAME = helper.get_config_parameter(CONFIG, "gcp_bq_dataset")
TOPIC_NAME = helper.get_config_parameter(CONFIG, "pub_sub_topic_name")


@functions_framework.cloud_event
def main_transform_load(cloud_event) -> None:
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


@functions_framework.cloud_event
def main_extract(cloud_event) -> None:
    run_parameters = helper.decode_event_messages(cloud_event.data)
    helper.check_parameters(run_parameters)

    user_id = run_parameters["user_id"]
    date = helper.get_date(run_parameters)
    endpoints = helper.get_endpoints(run_parameters)

    helper.call_api(
        date,
        user_id,
        endpoints,
        PROJECT_ID,
        BUCKET_NAME_CREDENTIALS,
        BUCKET_NAME_FILE_STORE,
    )
