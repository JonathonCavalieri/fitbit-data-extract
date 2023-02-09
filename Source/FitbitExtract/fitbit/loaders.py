from typing import Protocol
import os
import json
import re

from google.cloud import storage
from google.cloud import bigquery


class DataLoader(Protocol):
    def extract(self, path: str) -> dict:
        """Extract method for DataLoader Protocol"""

    def load(self, data: list[dict], name: str) -> None:
        """Load method for DataLoader Protocol"""


class LocalDataLoader:
    def extract(self, path: str) -> dict:
        _, file_extension = os.path.splitext(path)

        if file_extension == ".json":
            return self._extract_json(path)

        if file_extension in [".xml", ".tcx"]:
            return self._extract_xml(path)

        raise ValueError(f"file type {file_extension} is not supported")

    def _extract_xml(self, path: str):
        with open(path, "r") as file:
            data = file.read()
        return {"xml_data": data}

    def _extract_json(self, path: str):

        with open(path, "r") as file:
            data = json.load(file)

        return data

    def load(self, data: list[dict], name: str) -> None:

        for row in data:
            print(name, row)


class GCPDataLoader:
    def __init__(self, project_id: str, bucket_name: str, dataset_name: str) -> None:
        self.bucket_name = bucket_name
        self.project_id = project_id
        self.storage_client = storage.Client(project=project_id)
        self.bigquery_client = bigquery.Client(project=project_id)
        self.bucket = self.storage_client.get_bucket(bucket_name)
        self.dataset_name = dataset_name

        self.date_pattern = re.compile(
            "^20[0-9]{2}-((0[1-9])|(1[0-2]))-([0-2][1-9]|3[0-1])$"
        )

    def extract(self, path: str) -> dict:
        _, file_extension = os.path.splitext(path)

        blob = self.bucket.blob(path)
        assert blob.exists()
        file_data = blob.download_as_text()
        if file_extension == ".json":
            # return ast.literal_eval(file_data)
            return json.loads(file_data)

        if file_extension in [".xml", ".tcx"]:
            return {"xml_data": file_data}

        raise ValueError(f"file type {file_extension} is not supported")

    def load(self, data: list[dict], name: str) -> None:

        if not data or data == []:
            return None

        table_name = f"{self.project_id}.{self.dataset_name}.{name}"

        errors = self.bigquery_client.insert_rows_json(table_name, data)

        if not errors:
            print(f"New rows have been added to table {table_name}")
        else:
            raise ValueError(
                f"Encountered errors while inserting rows into table: {name} \nErrors:\n {errors}"
            )
