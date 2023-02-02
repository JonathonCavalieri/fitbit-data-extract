from datetime import datetime
from collections.abc import MutableMapping
import os
import re
from fitbit.loaders import DataLoader
from fitbit.messenger import Messenger
from fitbit.caller import EndpointParameters
import fitbit.constants as constants
import xml.etree.ElementTree as ET


def flattern_dictionary(d, parent_key="", sep=".") -> dict:
    items = []
    for key, value in d.items():
        new_key = parent_key + sep + key if parent_key else key
        if isinstance(value, MutableMapping):
            items.extend(flattern_dictionary(value, new_key, sep=sep).items())
        else:
            items.append((new_key, value))
    return dict(items)


def clean_datetime(datetime_fields: list, data: dict) -> dict:
    for datetime_field in datetime_fields:
        if datetime_field in data:
            data[datetime_field] = data[datetime_field][:19].replace("T", " ")

    return data


def clean_time(time_fields: list, data: dict) -> dict:
    for time_field in time_fields:
        if time_field in data:
            data[time_field] = data[time_field] + ":00"

    return data


def convert_to_number(string_value: str):
    try:
        return int(string_value)
    except ValueError:
        try:
            return float(string_value)
        except ValueError:
            return string_value


class FitbitETL:
    def __init__(self, data_loader: DataLoader, messenger: Messenger) -> None:
        self.data_loader = data_loader
        self.available_endpoint_parsers = {
            "get_heart_rate_by_date": self._transform_load_heart_rate_data,
            "get_body_weight_by_date": self._transform_load_body_weight_data,
            "get_activity_summary_by_date": self._transform_load_summary_data,
            "get_sleep_by_date": self._transform_load_sleep_data,
            "get_cardio_score_by_date": self._transform_load_cardioscore_data,
            "get_activity_tcx_by_id": self._transform_load_activity_tcx_data,
        }
        self.processing_datetime = datetime.now().strftime(constants.DATETIME_FORMAT)
        self.additional_api_calls = []
        self.user_id = None
        self.path = None
        self.endpoint = None
        self.date = None
        self.instance_id = None
        self.messenger = messenger

    def process(self, path: str) -> None:
        self.get_details_from_path(path)
        data = self.extract_data()
        self.transform_load_data(data)
        self.log_processing()
        self.call_additional_endpoints()

    def get_details_from_path(self, path: str) -> str:

        file_name = os.path.basename(path)
        endpoint_search = re.search(".*(get.+)_(.+)\..+", file_name, re.IGNORECASE)

        if endpoint_search:
            self.endpoint = endpoint_search.group(1)
            self.user_id = endpoint_search.group(2)
        else:
            raise ValueError(
                "Could not parse endpoint and user from filename, should be of format [endpoint]_[user id].format"
            )

        if self.endpoint not in self.available_endpoint_parsers:
            raise KeyError(f"{self.endpoint} is not in the available endpoint parsers")

        try:
            folder_name = os.path.basename(os.path.dirname(path))
            self.date = datetime.strptime(folder_name, "%Y%m%d").date()

        except ValueError as exc:
            raise ValueError(
                "Could not parse date from path, should be of format /[date]/[filename].format"
            ) from exc

        self.path = path

        instance_id_search = re.search("([0-9]+)_get.+", file_name, re.IGNORECASE)

        if instance_id_search:
            self.instance_id = int(instance_id_search.group(1))

    def extract_data(self) -> dict:
        if self.path is None:
            raise ValueError("Set path variable before processing data")

        return self.data_loader.extract(self.path)

    def transform_load_data(self, input_data: dict) -> None:

        if self.user_id is None:
            raise ValueError("Set user_id variable before processing data")
        if self.endpoint is None:
            raise ValueError("Set endpoint variable before processing data")
        if self.date is None:
            raise ValueError("Set date variable before processing data")

        self.available_endpoint_parsers[self.endpoint](input_data)

    def call_additional_endpoints(self) -> None:
        message_data = self.messenger.prep_message(
            self.additional_api_calls,
            self.user_id,
            self.date.strftime(constants.DATE_FORMAT),
        )

        self.messenger.send_message(message_data)

    def log_processing(self) -> None:

        log_dict = {
            "date": self.date.strftime(constants.DATE_FORMAT),
            "user_id": self.user_id,
            "processed_date": self.processing_datetime,
            "api_endpoint": self.endpoint,
            "file_processed": self.path,
        }

        table_name = constants.TABLE_NAME_MAPPING["file_processing_log"]
        self.data_loader.load([log_dict], table_name)

    ###########################################################
    # Methods for parsing individual endpoints or sub objects #
    ###########################################################

    def _transform_dict_from_metadata(
        self,
        data: dict,
        fields: list,
        datetime_fields: list = None,
        append_date: bool = True,
        append_user_id: bool = True,
        append_processed_date: bool = True,
        time_fields: list = None,
    ) -> dict:

        if datetime_fields is not None:
            data = clean_datetime(datetime_fields, data)

        if time_fields is not None:
            data = clean_time(time_fields, data)

        data = flattern_dictionary(data)
        temp_dict = {
            fields[key]["bq_name"]: value
            for key, value in data.items()
            if key in fields
        }

        if "date" not in temp_dict and append_date:
            temp_dict["date"] = self.date.strftime(constants.DATE_FORMAT)

        if append_user_id:
            temp_dict["user_id"] = self.user_id

        if append_processed_date:
            temp_dict["processed_date"] = self.processing_datetime

        return temp_dict

    def _transform_activities(self, activities: list) -> list:
        output_data = []

        for activity in activities:
            url_kwargs = {"log_id": activity["logId"]}
            tcx_endpoint = EndpointParameters(
                "get_activity_tcx_by_id", "GET", "tcx", url_kwargs=url_kwargs
            )
            self.additional_api_calls.append(tcx_endpoint)
            temp_dict = self._transform_dict_from_metadata(
                activity, constants.ACTIVITY_FIELDS, time_fields=["startTime"]
            )
            temp_dict["last_modified"] = temp_dict["last_modified"][:19].replace(
                "T", " "
            )
            output_data.append(temp_dict)

        return output_data

    def _transform_load_summary_data(self, input_data: dict) -> None:

        if "activities" not in input_data:
            raise KeyError("Summary data is missing activities object")
        if "goals" not in input_data:
            raise KeyError("Summary data is missing goals object")
        if "summary" not in input_data:
            raise KeyError("Summary data is missing summary object")

        # Activities  section of summary response
        activities = self._transform_activities(input_data["activities"])
        table_name = constants.TABLE_NAME_MAPPING[f"{self.endpoint}_activity"]
        self.data_loader.load(activities, table_name)

        # Goals section of summary response
        goals = self._transform_dict_from_metadata(
            input_data["goals"], constants.GOAL_FIELDS
        )
        table_name = constants.TABLE_NAME_MAPPING[f"{self.endpoint}_goals"]
        self.data_loader.load([goals], table_name)

        # Summary stats for day
        summary = input_data["summary"].copy()

        for distance in input_data["summary"]["distances"]:
            distance_name = distance["activity"]
            summary[f"{distance_name}_distance"] = distance["distance"]

        summary = self._transform_dict_from_metadata(summary, constants.SUMMARY_FIELDS)
        table_name = constants.TABLE_NAME_MAPPING[self.endpoint]
        self.data_loader.load([summary], table_name)

    def _transform_load_body_weight_data(self, input_data: dict) -> None:

        if "weight" not in input_data:
            raise KeyError("Weight data is missing weight object")

        if len(input_data["weight"]) > 0:
            # If no weight is logged it just contains an empty list
            # If multiple weights are logged only seems to return latest
            summary = self._transform_dict_from_metadata(
                input_data["weight"][0], constants.WEIGHT_FIELDS
            )
            table_name = constants.TABLE_NAME_MAPPING[self.endpoint]
            self.data_loader.load([summary], table_name)

    def _transform_load_heart_rate_data(self, input_data: dict) -> None:

        if "activities-heart" not in input_data:
            raise KeyError(
                "Expected activities-heart to be in heart rate data dictionary"
            )

        output_data = []

        for row in input_data["activities-heart"]:
            temp_dict = row.copy()
            for zone in row["value"]["heartRateZones"]:
                zone_name = zone["name"].lower().replace(" ", "_")

                temp_dict[f"{zone_name}_calories"] = zone["caloriesOut"]
                temp_dict[f"{zone_name}_minutes"] = zone["minutes"]

            temp_dict = self._transform_dict_from_metadata(
                temp_dict, constants.HEART_RATE_FIELDS
            )
            output_data.append(temp_dict)

        table_name = constants.TABLE_NAME_MAPPING[self.endpoint]
        self.data_loader.load(output_data, table_name)

    def _transform_sleep_detail(self, sleep_details: dict, log_id: int) -> list[dict]:

        sleep_details_combine = sleep_details["data"] + sleep_details["shortData"]
        return_list = []
        for row in sleep_details_combine:
            new_row = self._transform_dict_from_metadata(
                row, constants.SLEEP_DETAILS_FIELDS, ["dateTime"], False, False, False
            )
            new_row["log_id"] = log_id
            return_list.append(new_row)

        return return_list

    def _transform_load_sleep_data(self, input_data: dict) -> None:

        if "sleep" not in input_data:
            raise KeyError("Expected sleep to be in sleep data dictionary")

        output_data = []
        output_data_details = []

        for row in input_data["sleep"]:

            temp_dict = self._transform_dict_from_metadata(row, constants.SLEEP_FIELDS)
            output_data.append(temp_dict)

            details_list = self._transform_sleep_detail(row["levels"], row["logId"])
            output_data_details.extend(details_list)

        table_name = constants.TABLE_NAME_MAPPING[self.endpoint]
        self.data_loader.load(output_data, table_name)
        self.data_loader.load(output_data_details, f"{table_name}_detail")

    def _transform_load_cardioscore_data(self, input_data: dict) -> None:
        if "cardioScore" not in input_data:
            raise KeyError("Expected cardioScore to be in cardio score data dictionary")

        output_data = []

        for row in input_data["cardioScore"]:
            temp_dict = self._transform_dict_from_metadata(
                row, constants.CARDIOSCORE_FIELDS
            )
            output_data.append(temp_dict)

        table_name = constants.TABLE_NAME_MAPPING[self.endpoint]
        self.data_loader.load(output_data, table_name)

    def _transform_load_activity_tcx_data(self, input_data: dict) -> None:

        if self.instance_id is None:
            raise ValueError("Instance Id is not instantiated")

        output_data = []
        root = ET.fromstring(input_data["xml_data"])
        tag_prefix = "{http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2}"

        for activity in root.iter(f"{tag_prefix}Activity"):
            activity_attrib = activity.attrib
            activity_attrib["log_id"] = self.instance_id
            for lap_number, lap in enumerate(activity.iter(f"{tag_prefix}Lap")):
                lap_list = self._transform_activity_lap(
                    lap, lap_number, tag_prefix, activity_attrib
                )
                output_data += lap_list

        table_name = constants.TABLE_NAME_MAPPING[self.endpoint]
        self.data_loader.load(output_data, table_name)

    def _transform_activity_track_point(
        self, track_point: ET.Element, point_number: int, tag_prefix: str
    ) -> dict:
        track_point_dict = {"point_order": point_number}
        for child in track_point:
            # Handle positions and sub object
            if child.tag == f"{tag_prefix}Position":
                for position in child:
                    tag = position.tag.replace(tag_prefix, "")
                    track_point_dict[tag] = convert_to_number(position.text)
                continue
            # Handle heart rate sub object
            if child.tag == f"{tag_prefix}HeartRateBpm":
                tag = child.tag.replace(tag_prefix, "")
                track_point_dict[tag] = convert_to_number(child[0].text)
                continue
            # All Others
            tag = child.tag.replace(tag_prefix, "")
            track_point_dict[tag] = convert_to_number(child.text)
        return track_point_dict

    def _transform_activity_lap(
        self, lap: ET.Element, lap_number: int, tag_prefix: str, activity_attrib: dict
    ) -> list:
        return_list = []
        lap_dict = {"log_id": self.instance_id, "lap_number": lap_number}
        for lap_child in lap:
            tag = lap_child.tag.replace(tag_prefix, "")
            if tag != "Track":
                lap_dict[tag] = convert_to_number(lap_child.text)

        for point_number, track_point in enumerate(lap.iter(f"{tag_prefix}Trackpoint")):
            track_point_dict = self._transform_activity_track_point(
                track_point, point_number, tag_prefix
            )
            out_dict = activity_attrib | lap_dict | track_point_dict
            out_dict = self._transform_dict_from_metadata(
                out_dict, constants.ACTIVITY_TCX_FIELDS, ["Time"]
            )
            return_list.append(out_dict)
        return return_list
