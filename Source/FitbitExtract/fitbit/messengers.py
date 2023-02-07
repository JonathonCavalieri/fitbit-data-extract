from dataclasses import asdict
import json
from typing import Protocol
from fitbit.caller import EndpointParameters
from google.cloud import pubsub_v1


class Messenger(Protocol):
    def prep_message(
        self, messages: list[EndpointParameters], user_id: str, date: str
    ) -> str:
        """prep_message method for Messenger Protocol"""

    def send_message(self, message: str) -> str:
        """send_message method for Messenger Protocol"""


class LocalMessenger:
    def prep_message(
        self, messages: list[EndpointParameters], user_id: str, date: str
    ) -> str:
        if messages == ['all']:
            endpoint_messages = ['all']
        else:
            endpoint_messages = []
            for message in messages:
                endpoint_messages.append(asdict(message))


        pubsub_message = {
            "user_id": user_id,
            "date": date,
            "endpoints": endpoint_messages,
        }
        if endpoint_messages == []:
            return None
        return json.dumps(pubsub_message).encode("utf-8")

    def send_message(self, message: str) -> str:
        if message is not None:
            print(f"sending message: {message}")
            return "success"


class PubSubMessenger:
    def __init__(self, project_id: str, topic_name: str) -> None:
        self.pubsub_client = pubsub_v1.PublisherClient()
        self.topic_name = self.pubsub_client.topic_path(project_id, topic_name)
        # self.topic = self.pubsub_client.get_topic(topic=self.topic_name)

    def prep_message(
        self, messages: list[EndpointParameters], user_id: str, date: str
    ) -> str:
        
        if messages == ['all']:
            endpoint_messages = ['all']
        else:
            endpoint_messages = []
            for message in messages:
                endpoint_messages.append(asdict(message))

        pubsub_message = {
            "user_id": user_id,
            "date": date,
            "endpoints": endpoint_messages,
        }
        if endpoint_messages == []:
            return None
        return json.dumps(pubsub_message).encode("utf-8")

    def send_message(self, message: str) -> str:
        if message is not None:
            future = self.pubsub_client.publish(self.topic_name, message)
            message_id = future.result()
            print(
                f"Publishing message {message} to topic {self.topic_name} message id: {message_id}"
            )
            return message_id
