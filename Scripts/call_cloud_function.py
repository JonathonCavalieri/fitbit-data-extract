import sys
from time import sleep

sys.path.append("Source/FitbitExtract")
from fitbit.messengers import PubSubMessenger
from helper.functions import get_config_parameter

CONFIG_DIRECTORY = "config.json"
PROJECT_ID = get_config_parameter(CONFIG_DIRECTORY, "gcp_project")
TOPIC = get_config_parameter(CONFIG_DIRECTORY, "pub_sub_topic_name")

USER = get_config_parameter(CONFIG_DIRECTORY, "user_id")


def send_messages():
    print(f"publishing messages to topic: {TOPIC} in project: {PROJECT_ID}")
    dates = [f"2023-01-{i:02d}" for i in range(1,32)]
    dates += [f"2023-01-{i:02d}" for i in range(1,6)]
    pubsub_messenger = PubSubMessenger(PROJECT_ID, TOPIC)
    for date in dates:
        print(f"Sending message for user: {USER} on date: {date}")
        message = pubsub_messenger.prep_message(['all'], USER, date)
        pubsub_messenger.send_message(message)
        sleep(150)

if __name__ == "__main__":
    send_messages()