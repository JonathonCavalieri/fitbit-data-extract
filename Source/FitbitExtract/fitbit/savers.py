import os
from typing import Protocol
from google.cloud import storage


class FitbitResponseSaver(Protocol):
    """
    Interface protocol for a Fitbit Response Saver. These classes will be used to save
    the different response to different locations

    Methods
    save(str, str, str, str) -> None: Save the response to the target location
    """

    def save(
        self, response: str, folder: str, file_name: str, file_format: str
    ) -> None:
        """Save the response to the target location"""


class LocalResponseSaver:
    def __init__(self, base_location, make_directory=True) -> None:
        self.base_location = base_location
        self.make_directory = make_directory

    def save(
        self, response: str, folder: str, file_name: str, file_format: str
    ) -> None:
        """Saves the response to a local directory

        Args:
            response (str): response data in plain text format
            folder (str): folder location to save file to
            file_name (str): File name when saving
            file_format (str): File format extention
        """
        directory = f"{self.base_location}/{folder}"
        full_path = f"{directory}/{file_name}.{file_format}"

        if not os.path.exists(directory) and self.make_directory:
            os.makedirs(directory)

        with open(full_path, "w", encoding="utf-8") as file:
            file.write(response)


class GCPResponseSaver:
    def __init__(self, bucket_name, project_id) -> None:
        self.bucket_name = bucket_name
        self.storage_client = storage.Client(project=project_id)
        self.bucket = self.storage_client.get_bucket(bucket_name)

    def save(
        self, response: str, folder: str, file_name: str, file_format: str
    ) -> None:
        """Saves the response to a Google Cloud Storage Bucket

        Args:
            response (str): response data in plain text format
            folder (str): folder location to save file to
            file_name (str): File name when saving
            file_format (str): File format extention
        """
        blob_name = f"{folder}/{file_name}.{file_format}"

        blob = self.bucket.blob(blob_name)

        blob.upload_from_string(response)
