import sys

sys.path.append("Source/FitbitExtract")
from helper.functions import get_config_parameter
from google.cloud import storage, pubsub

CONFIG_DIRECTORY = "config.json"
PROJECT_ID = get_config_parameter(CONFIG_DIRECTORY, "gcp_project")
LOCATION = get_config_parameter(CONFIG_DIRECTORY, "gcp_location")

buckets = [
    "fitbit-data-extract-credentials",
    "fitbit-data-extract-data-files",
    "fitbit-data-extract-deploy-staging",
]
storage_client = storage.Client(project=PROJECT_ID)
for bucket_name in buckets:
    bucket = storage_client.bucket(bucket_name)

    if not bucket.exists():
        bucket.iam_configuration.uniform_bucket_level_access_enabled = True
        new_bucket = storage_client.create_bucket(bucket, location=LOCATION)

topic_name = f"{PROJECT_ID}-buffer"
pubsub_client = pubsub.PublisherClient()
project_path = f"projects/{PROJECT_ID}"
topics = pubsub_client.list_topics(request={"project": project_path})
topic_exists = any(topic.name for topic in topics if topic.name.endswith(topic_name))

if not topic_exists:
    topic_path = pubsub_client.topic_path(PROJECT_ID, topic_name)
    pubsub_client.create_topic(request={"name": topic_path})
