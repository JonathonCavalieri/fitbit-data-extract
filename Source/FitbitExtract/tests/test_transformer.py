import re
from datetime import datetime
import pytest
from tests.fixtures import transformer, loader, messenger
from tests.fixtures import test_data_path, test_data_path_tcx, session_temp
from tests.fixtures import testing_data_dictionarys
from fitbit.caller import EndpointParameters

from fitbit import transformers


def test_flattern_dictionary() -> None:
    """Tests flattern dictionary functions"""
    dictionary = {
        "test1": "value1",
        "test2": {"nested1": "nested_value1"},
        "test3": {"nested2": "nested_value2"},
        "test4": {
            "nested3": "nested_value3",
            "nested4": {"secondnested1": "secondnested_value1"},
        },
    }
    expected_result = {
        "test1": "value1",
        "test2.nested1": "nested_value1",
        "test3.nested2": "nested_value2",
        "test4.nested3": "nested_value3",
        "test4.nested4.secondnested1": "secondnested_value1",
    }

    assert transformers.flattern_dictionary(dictionary) == expected_result


def test_clean_datetime() -> None:
    """Tests clean datetime function"""
    data = {"datetime": "2023-01-01T12:12:12.00000"}
    expected_result = "2023-01-01 12:12:12"
    result = transformers.clean_datetime(["datetime"], data)
    assert result["datetime"] == expected_result


def test_clean_time() -> None:
    """Tests clean time function"""
    data = {"time": "12:12"}
    expected_result = "12:12:00"
    result = transformers.clean_time(["time"], data)
    assert result["time"] == expected_result


def test_convert_number() -> None:
    """Tests convert number function"""

    assert transformers.convert_to_number("1") == 1
    assert transformers.convert_to_number("1.0") == 1.0
    assert transformers.convert_to_number("hello") == "hello"
    assert transformers.convert_to_number("-1000.2032") == -1000.2032
    assert transformers.convert_to_number("-65") == -65
    assert transformers.convert_to_number("123 hello") == "123 hello"


############################
# Test the FitBitETL Class #
############################


def test_get_details_from_path(transformer) -> None:
    """Tests the get details from path method of FitBitETL class"""
    user_id = "TEST123"
    endpoint = "get_activity_tcx_by_id"
    instance_id = 53177087392
    date = "20230118"
    path = f"{endpoint}/{date}/{instance_id}_{endpoint}_{user_id}.tcx"

    transformer.get_details_from_path(path)

    assert transformer.user_id == user_id
    assert transformer.endpoint == endpoint
    assert transformer.instance_id == instance_id
    assert transformer.date == datetime.strptime(date, "%Y%m%d").date()


def test_get_details_from_path_bad_endpoint(transformer) -> None:
    """Tests the get details from path method of FitBitETL class for none valid endpoint string"""
    user_id = "TEST123"
    endpoint = "activity_tcx_by_id"
    gcs_path = f"{endpoint}/20230118/{endpoint}_{user_id}.tcx"
    pattern = re.escape(
        "Could not parse endpoint and user from filename, should be of format [endpoint]_[user id].format"
    )
    with pytest.raises(ValueError, match=pattern):
        transformer.get_details_from_path(gcs_path)


def test_get_details_from_path_bad_date(transformer) -> None:
    """Tests the get details from path method of FitBitETL class"""
    endpoint = "get_activity_tcx_by_id"
    gcs_path = f"{endpoint}/baddate/{endpoint}_TEST123.tcx"
    pattern = re.escape(
        "Could not parse date from path, should be of format /[date]/[filename].format with date as YYYYMMDD"
    )
    with pytest.raises(ValueError, match=pattern):
        transformer.get_details_from_path(gcs_path)


def test_get_details_from_path_endpoint_not_available(transformer) -> None:
    """Tests the get details from path method of FitBitETL class for endpoint that was correct format but is not in valid list"""
    user_id = "TEST123"
    endpoint = "get_fake_endpoint"
    gcs_path = f"{endpoint}/20230118/{endpoint}_{user_id}.tcx"
    pattern = f"{endpoint} is not in the available endpoint parsers"
    with pytest.raises(ValueError, match=pattern):
        transformer.get_details_from_path(gcs_path)


def test_extract_data(transformer, test_data_path) -> None:
    """Tests the extract data method of the FitBitETL class"""
    dirctory, expected_results = test_data_path
    transformer.path = dirctory
    results = transformer.extract_data()
    assert results == expected_results


def test_extract_data_path_not_set(transformer) -> None:
    """Tests the extract data method of the FitBitETL class when path has not been set"""

    with pytest.raises(ValueError, match="Set path variable before processing data"):
        transformer.extract_data()


def test_transform_load_data_user_not_set(transformer) -> None:
    """Tests the transform_load_data method of the FitBitETL class when user has not been set"""
    with pytest.raises(ValueError, match="Set user_id variable before processing data"):
        transformer.transform_load_data({})


def test_transform_load_data_endpoint_not_set(transformer) -> None:
    """Tests the transform_load_data method of the FitBitETL class when endpoint has not been set"""
    transformer.user_id = "test"
    with pytest.raises(
        ValueError, match="Set endpoint variable before processing data"
    ):
        transformer.transform_load_data({})


def test_transform_load_data_date_not_set(transformer) -> None:
    """Tests the transform_load_data method of the FitBitETL class when date has not been set"""
    transformer.user_id = "test"
    transformer.endpoint = "test"
    with pytest.raises(ValueError, match="Set date variable before processing data"):
        transformer.transform_load_data({})


def test_transform_load_data(transformer, capsys, test_data_path) -> None:
    """Tests the transform_load_data method of the FitBitETL class"""
    _, data = test_data_path
    transformer.date = datetime.now().date()
    transformer.user_id = "TESTUSER"
    transformer.endpoint = "get_cardio_score_by_date"
    transformer.transform_load_data(data)
    captured = capsys.readouterr()

    expected_value = """cardioscore {'date': '2023-01-18', 'vo2_max': '44-48', 'user_id': 'TESTUSER', 'processed_date': '2023-02-03 12:31:38'}
"""
    assert captured.out == expected_value


def test_call_additional_endpoints(transformer, capsys) -> None:
    """Tests the call_additional_endpoints method of the FitBitETL class"""
    endpoints = [EndpointParameters("test1"), EndpointParameters("test2")]
    transformer.additional_api_calls = endpoints
    transformer.date = datetime.now().date()
    transformer.call_additional_endpoints()

    captured = capsys.readouterr()
    expected_value = """sending message: b'{"user_id": null, "date": "2023-02-03", "endpoints": [{"name": "test1", "method": "GET", "response_format": "json", "url_kwargs": {}, "body": {}, "headers": {}}, {"name": "test2", "method": "GET", "response_format": "json", "url_kwargs": {}, "body": {}, "headers": {}}]}'
"""
    assert captured.out == expected_value


def test_log_processing(transformer, capsys) -> None:
    """Tests the log_processing method of the FitBitETL class"""
    transformer.date = datetime.strptime("2023-01-01", "%Y-%m-%d").date()
    transformer.user_id = "TESTUSER"
    transformer.endpoint = "get_cardio_score_by_date"
    transformer.path = "20230101/get_cardio_score_by_date_TESTUSER.json"

    transformer.log_processing()
    captured = capsys.readouterr()
    expected_value = """files_processed {'date': '2023-01-01', 'user_id': 'TESTUSER', 'processed_date': '2023-02-03 12:31:38', 'api_endpoint': 'get_cardio_score_by_date', 'file_processed': '20230101/get_cardio_score_by_date_TESTUSER.json'}
"""
    assert captured.out == expected_value


def test_process(transformer, capsys, test_data_path) -> None:
    """Tests the _transform_load_cardioscore_data method of the FitBitETL class"""
    file_path, _ = test_data_path
    transformer.process(file_path)
    captured = capsys.readouterr()
    data_value = "cardioscore {'date': '2023-01-18', 'vo2_max': '44-48', 'user_id': 'TESTUSER', 'processed_date': '2023-02-03 12:31:38'}\n"
    log_value = (
        "files_processed {'date': '2023-01-18', 'user_id': 'TESTUSER', 'processed_date': '2023-02-03 12:31:38', 'api_endpoint': 'get_cardio_score_by_date', 'file_processed': '"
        + file_path
        + "'}\n"
    )
    expected_value = data_value + log_value
    assert captured.out.replace("\\\\", "\\") == expected_value


#############################################
# Test the FitBitETL Class transform Methods#
#############################################


def transform_test_helper(transformer, endpoint, data_dict):
    """Helper function to test the transform load methods in  the FitBitETL class"""
    data_details = data_dict[endpoint]

    transformer.user_id = data_details["user_id"]
    transformer.endpoint = endpoint
    transformer.date = data_details["date"]

    if "instance_id" in data_details:
        transformer.instance_id = data_details["instance_id"]
    # call the transform function for a particular endpoint
    transformer.available_endpoint_parsers[endpoint](data_details["data"])


def test_transform_load_cardioscore_data(
    transformer, capsys, testing_data_dictionarys
) -> None:
    """Tests the _transform_load_cardioscore_data method of the FitBitETL class"""

    endpoint = "get_cardio_score_by_date"
    transform_test_helper(transformer, endpoint, testing_data_dictionarys)
    captured = capsys.readouterr()
    expected_value = """cardioscore {'date': '2023-01-18', 'vo2_max': '44-48', 'user_id': 'TESTUSER', 'processed_date': '2023-02-03 12:31:38'}
"""
    assert captured.out == expected_value


def test_transform_load_cardioscore_data_bad_input(transformer) -> None:
    """Tests the _transform_load_cardioscore_data method of the FitBitETL class where missing key"""
    with pytest.raises(
        KeyError, match="Expected cardioScore to be in cardio score data dictionary"
    ):
        transformer._transform_load_cardioscore_data({})


def test_transform_load_body_weight_data(
    transformer, capsys, testing_data_dictionarys
) -> None:
    """Tests the _transform_load_body_weight_data method of the FitBitETL class"""

    endpoint = "get_body_weight_by_date"
    transform_test_helper(transformer, endpoint, testing_data_dictionarys)
    captured = capsys.readouterr()
    expected_value = """weight {'bmi': 25.93, 'date': '2023-01-17', 'log_id': 1673999999000, 'weight': 77.6, 'user_id': 'TESTUSER', 'processed_date': '2023-02-03 12:31:38'}
"""
    assert captured.out == expected_value


def test_transform_load_body_weight_data_bad_input(transformer) -> None:
    """Tests the _transform_load_summary_data method of the FitBitETL class where missing activities"""
    with pytest.raises(KeyError, match="Weight data is missing weight object"):
        transformer._transform_load_body_weight_data({})


def test_transform_load_heart_rate_data(
    transformer, capsys, testing_data_dictionarys
) -> None:
    """Tests the _transform_load_heart_rate_data method of the FitBitETL class"""

    endpoint = "get_heart_rate_by_date"
    transform_test_helper(transformer, endpoint, testing_data_dictionarys)
    captured = capsys.readouterr()
    expected_value = """heart_rate {'date': '2023-01-18', 'resting_heart_rate': 64, 'out_of_range_calories': 2315.26512, 'out_of_range_minutes': 1398, 'fat_burn_calories': 320.9723999999999, 'fat_burn_minutes': 34, 'cardio_calories': 86.69807999999999, 'cardio_minutes': 8, 'peak_calories': 0, 'peak_minutes': 0, 'user_id': 'TESTUSER', 'processed_date': '2023-02-03 12:31:38'}
"""
    assert captured.out == expected_value


def test_transform_load_heart_rate_data_bad_input(transformer) -> None:
    """Tests the _transform_load_heart_rate_data method of the FitBitETL class where missing activities"""
    with pytest.raises(
        KeyError, match="Expected activities-heart to be in heart rate data dictionary"
    ):
        transformer._transform_load_heart_rate_data({})


def test_transform_load_summary_data(
    transformer, capsys, testing_data_dictionarys
) -> None:
    """Tests the _transform_load_summary_data method of the FitBitETL class"""

    endpoint = "get_activity_summary_by_date"
    transform_test_helper(transformer, endpoint, testing_data_dictionarys)
    captured = capsys.readouterr()
    expected_value = """activity {'activity_id': 90013, 'activity_parent_id': 90013, 'activity_parent_name': 'Walk', 'calories': 371, 'description': 'Walking less than 2 mph, strolling very slowly', 'duration': 2229000, 'has_active_zone_minutes': True, 'has_start_time': True, 'is_favorite': False, 'last_modified': '2023-01-17 21:14:42', 'log_id': 53177087392, 'name': 'Walk', 'start_date': '2023-01-18', 'start_time': '07:06:00', 'steps': 4031, 'date': '2023-01-18', 'user_id': 'TESTUSER', 'processed_date': '2023-02-03 12:31:38'}
goals {'active_minutes': 30, 'calories_out': 2675, 'distance': 8.05, 'floors': 10, 'steps': 10000, 'date': '2023-01-18', 'user_id': 'TESTUSER', 'processed_date': '2023-02-03 12:31:38'}
summary {'active_score': -1, 'activity_calories': 1101, 'calories_bmr': 1705, 'calories_out': 2722, 'elevation': 60.96, 'fairly_active_minutes': 5, 'floors': 20, 'lightly_active_minutes': 157, 'marginal_calories': 673, 'resting_heart_rate': 64, 'sedentary_minutes': 698, 'steps': 7883, 'very_active_minutes': 52, 'total_distance': 6.46, 'tracker_distance': 6.46, 'logged_activities_distance': 3.70049, 'very_active_distance': 4.55, 'moderately_active_distance': 0.2, 'lightly_active_distance': 1.71, 'sedentary_active_distance': 0, 'date': '2023-01-18', 'user_id': 'TESTUSER', 'processed_date': '2023-02-03 12:31:38'}
"""
    assert captured.out == expected_value


def test_transform_load_summary_data_bad_input_activities(transformer) -> None:
    """Tests the _transform_load_summary_data method of the FitBitETL class where missing activities"""
    with pytest.raises(KeyError, match="Summary data is missing activities object"):
        transformer._transform_load_summary_data({})


def test_transform_load_summary_data_bad_input_summary(transformer) -> None:
    """Tests the _transform_load_summary_data method of the FitBitETL class"""
    with pytest.raises(KeyError, match="Summary data is missing summary object"):
        transformer._transform_load_summary_data({"activities": "dummy_value"})


def test_transform_load_sleep_data(
    transformer, capsys, testing_data_dictionarys
) -> None:
    """Tests the _transform_load_sleep_data method of the FitBitETL class"""

    endpoint = "get_sleep_by_date"
    transform_test_helper(transformer, endpoint, testing_data_dictionarys)
    captured = capsys.readouterr()
    expected_value = """sleep {'date': '2023-01-18', 'duration': 27600000, 'efficiency': 88, 'end_time': '2023-01-18T06:25:00.000', 'info_code': 0, 'is_main_sleep': True, 'log_id': 39842924697, 'log_type': 'auto_detected', 'minutes_after_wakeup': 4, 'minutes_asleep': 385, 'minutes_awake': 75, 'minutes_to_fall_asleep': 0, 'start_time': '2023-01-17T22:45:00.000', 'time_in_bed': 460, 'type': 'stages', 'user_id': 'TESTUSER', 'processed_date': '2023-02-03 12:31:38'}
sleep_detail {'date_time': '2023-01-17 22:45:00', 'level': 'wake', 'seconds': 990, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-17 23:01:30', 'level': 'light', 'seconds': 1200, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-17 23:21:30', 'level': 'deep', 'seconds': 510, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-17 23:30:00', 'level': 'light', 'seconds': 1350, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-17 23:52:30', 'level': 'deep', 'seconds': 1170, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 00:12:00', 'level': 'light', 'seconds': 600, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 00:22:00', 'level': 'rem', 'seconds': 1380, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 00:45:00', 'level': 'light', 'seconds': 2850, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 01:32:30', 'level': 'deep', 'seconds': 1080, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 01:50:30', 'level': 'light', 'seconds': 960, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 02:06:30', 'level': 'wake', 'seconds': 420, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 02:13:30', 'level': 'light', 'seconds': 150, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 02:16:00', 'level': 'rem', 'seconds': 1800, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 02:46:00', 'level': 'wake', 'seconds': 420, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 02:53:00', 'level': 'light', 'seconds': 3480, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 03:51:00', 'level': 'rem', 'seconds': 2940, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 04:40:00', 'level': 'light', 'seconds': 1380, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 05:03:00', 'level': 'deep', 'seconds': 1680, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 05:31:00', 'level': 'light', 'seconds': 240, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 05:35:00', 'level': 'rem', 'seconds': 1050, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 05:52:30', 'level': 'wake', 'seconds': 390, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 05:59:00', 'level': 'light', 'seconds': 840, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 06:13:00', 'level': 'wake', 'seconds': 720, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-17 23:04:30', 'level': 'wake', 'seconds': 30, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-17 23:07:00', 'level': 'wake', 'seconds': 120, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-17 23:10:30', 'level': 'wake', 'seconds': 120, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-17 23:15:00', 'level': 'wake', 'seconds': 30, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-17 23:30:00', 'level': 'wake', 'seconds': 30, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-17 23:48:00', 'level': 'wake', 'seconds': 30, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 00:10:30', 'level': 'wake', 'seconds': 90, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 00:44:30', 'level': 'wake', 'seconds': 30, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 00:46:30', 'level': 'wake', 'seconds': 30, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 01:24:30', 'level': 'wake', 'seconds': 30, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 01:48:30', 'level': 'wake', 'seconds': 120, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 01:52:30', 'level': 'wake', 'seconds': 30, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 01:58:30', 'level': 'wake', 'seconds': 60, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 02:02:30', 'level': 'wake', 'seconds': 90, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 02:16:00', 'level': 'wake', 'seconds': 60, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 02:26:30', 'level': 'wake', 'seconds': 30, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 02:35:00', 'level': 'wake', 'seconds': 30, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 02:38:00', 'level': 'wake', 'seconds': 30, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 02:41:00', 'level': 'wake', 'seconds': 30, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 02:43:00', 'level': 'wake', 'seconds': 30, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 03:01:00', 'level': 'wake', 'seconds': 30, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 03:12:00', 'level': 'wake', 'seconds': 120, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 03:16:00', 'level': 'wake', 'seconds': 60, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 03:31:30', 'level': 'wake', 'seconds': 30, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 03:46:30', 'level': 'wake', 'seconds': 30, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 04:28:00', 'level': 'wake', 'seconds': 30, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 04:45:30', 'level': 'wake', 'seconds': 30, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 05:29:00', 'level': 'wake', 'seconds': 120, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 05:49:30', 'level': 'wake', 'seconds': 30, 'log_id': 39842924697}
sleep_detail {'date_time': '2023-01-18 06:06:30', 'level': 'wake', 'seconds': 60, 'log_id': 39842924697}
"""

    assert captured.out == expected_value


def test_transform_load_sleep_data_bad_input(transformer) -> None:
    """Tests the _transform_load_sleep_data method of the FitBitETL class where missing activities"""
    with pytest.raises(KeyError, match="Expected sleep to be in sleep data dictionary"):
        transformer._transform_load_sleep_data({})


def test_transform_load_activity_tcx_data(
    transformer, capsys, testing_data_dictionarys
) -> None:
    """Tests the _transform_load_activity_tcx_data method of the FitBitETL class"""

    endpoint = "get_activity_tcx_by_id"
    transform_test_helper(transformer, endpoint, testing_data_dictionarys)
    captured = capsys.readouterr()
    expected_value = """activity_detail {'sport': 'Other', 'log_id': 53177087392, 'lap_number': 0, 'total_time_seconds': 663.0, 'distance_meters': 0.0, 'calories': 107, 'intensity': 'Active', 'trigger_method': 'Manual', 'point_order': 0, 'date_time': '2023-01-18 07:06:17', 'latitude': -33.89657151699066, 'longitude': 151.1981600522995, 'altitude_meters': 43.580799998146816, 'heart_rate_bpm': 102, 'date': '2023-01-18', 'user_id': 'TESTUSER', 'processed_date': '2023-02-03 12:31:38'}
activity_detail {'sport': 'Other', 'log_id': 53177087392, 'lap_number': 1, 'total_time_seconds': 563.0, 'distance_meters': 1004.7700000000002, 'calories': 96, 'intensity': 'Active', 'trigger_method': 'Manual', 'point_order': 0, 'date_time': '2023-01-18 07:17:45', 'latitude': -33.888354539871216, 'longitude': 151.20156371593475, 'altitude_meters': 52.347969368935196, 'heart_rate_bpm': 127, 'date': '2023-01-18', 'user_id': 'TESTUSER', 'processed_date': '2023-02-03 12:31:38'}
activity_detail {'sport': 'Other', 'log_id': 53177087392, 'lap_number': 2, 'total_time_seconds': 594.0, 'distance_meters': 2007.39, 'calories': 106, 'intensity': 'Active', 'trigger_method': 'Manual', 'point_order': 0, 'date_time': '2023-01-18 07:27:09', 'latitude': -33.87998628616333, 'longitude': 151.20518672466278, 'altitude_meters': 31.50541212076629, 'heart_rate_bpm': 132, 'date': '2023-01-18', 'user_id': 'TESTUSER', 'processed_date': '2023-02-03 12:31:38'}
activity_detail {'sport': 'Other', 'log_id': 53177087392, 'lap_number': 3, 'total_time_seconds': 407.0, 'distance_meters': 3010.79, 'calories': 60, 'intensity': 'Active', 'trigger_method': 'Manual', 'point_order': 0, 'date_time': '2023-01-18 07:37:03', 'latitude': -33.87146699428558, 'longitude': 151.2072845697403, 'altitude_meters': 46.46037123643947, 'heart_rate_bpm': 134, 'date': '2023-01-18', 'user_id': 'TESTUSER', 'processed_date': '2023-02-03 12:31:38'}
"""
    assert captured.out == expected_value


def test_transform_load_activity_tcx_data_no_instance_id(transformer) -> None:
    """Tests the _transform_load_activity_tcx_data method of the FitBitETL class where missing activities"""
    with pytest.raises(ValueError, match="Instance Id is not instantiated"):
        transformer._transform_load_activity_tcx_data({})
    # with open("local_data/data/temp.txt", "w") as file:
    #     file.write(captured.out)


# datetime.strptime("2023-02-03 12:31:38", "%Y-%m-%d %H:%M:%S")
