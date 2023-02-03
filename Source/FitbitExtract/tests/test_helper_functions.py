import pytest
import base64
import json
from datetime import date, timedelta, datetime

from fitbit.caller import EndpointParameters
import helper.functions as helper
import helper.constants as constants

from tests.fixtures import config_file


def test_decode_event_messages() -> None:
    """_summary_"""
    test_message = {"test_key": "test_value"}
    test_message_encoded = json.dumps(test_message).encode("utf-8")
    test_message_data = {"message": {"data": base64.b64encode(test_message_encoded)}}
    assert test_message == helper.decode_event_messages(test_message_data)


def test_decode_event_messages_bad_dict() -> None:
    """_summary_"""
    test_message = b"This is a bad message"
    test_message_data = {"message": {"data": base64.b64encode(test_message)}}

    with pytest.raises(
        Exception, match="Could not parse pubsub message: .* into a dict"
    ):
        helper.decode_event_messages(test_message_data)


def test_check_parameters_date() -> None:
    """_summary_"""
    parameters = {"user_id": "test", "endpoints": "test"}
    with pytest.raises(KeyError, match="date was not provided in message body"):
        helper.check_parameters(parameters)


def test_check_parameters_user_id() -> None:
    """_summary_"""
    parameters = {"date": "test", "endpoints": "test"}
    with pytest.raises(KeyError, match="user_id was not provided in message body"):
        helper.check_parameters(parameters)


def test_check_parameters_endpoints() -> None:
    """_summary_"""
    parameters = {"user_id": "test", "date": "test"}
    with pytest.raises(KeyError, match="endpoints was not provided in message body"):
        helper.check_parameters(parameters)


def test_get_date_current() -> None:
    """_summary_"""
    parameters = {"date": "current"}
    expected_date = date.today() - timedelta(days=1)

    assert expected_date == helper.get_date(parameters)


def test_get_date() -> None:
    """_summary_"""
    parameters = {"date": "2022-03-03"}
    expected_date = datetime.strptime(parameters["date"], "%Y-%m-%d").date()

    assert expected_date == helper.get_date(parameters)


def test_get_endpoints_not_list() -> None:
    """_summary_"""
    parameters = {"endpoints": "test"}
    with pytest.raises(
        ValueError, match="Endpoints should be passed as a list even for a single value"
    ):
        helper.get_endpoints(parameters)


def test_get_endpoints_all() -> None:
    """_summary_"""
    parameters = {"endpoints": ["all"]}

    assert constants.ENDPOINTS == helper.get_endpoints(parameters)


def test_get_endpoints() -> None:
    """_summary_"""

    endpoint_1 = {
        "name": "test_name",
        "method": "GET",
        "response_format": "json",
        "url_kwargs": {},
        "headers": {},
        "body": {},
    }
    endpoint_2 = {
        "name": "test_name_2",
        "method": "POST",
        "response_format": "xml",
        "url_kwargs": {"test": "test"},
        "headers": {"test": "test"},
        "body": {"test": "test"},
    }
    expected_result = [
        EndpointParameters(**endpoint_1),
        EndpointParameters(**endpoint_2),
    ]
    parameters = {"endpoints": [endpoint_1, endpoint_2]}

    assert expected_result == helper.get_endpoints(parameters)


def test_get_config_parameter(config_file) -> None:
    """Test the get_config_parameter help function"""
    parameter_name = "test_parameter_2"
    expected_value = "parameter_value_2"
    value = helper.get_config_parameter(config_file, parameter_name)
    assert value == expected_value


def test_get_config_parameter_bad_parameter_name(config_file) -> None:
    """Test the get_config_parameter help function when bad parameter"""
    parameter_name = "bad_parameter"
    with pytest.raises(KeyError, match=f"Please add to {parameter_name}"):
        helper.get_config_parameter(config_file, parameter_name)


def test_get_config_parameter_bad_missing_file() -> None:
    """Test the get_config_parameter help function when bad parameter"""
    config_file = "baddirectory/badconfig.json"
    parameter_name = "bad_parameter"
    with pytest.raises(Exception, match=f"No config file found at {config_file}"):
        helper.get_config_parameter(config_file, parameter_name)


def test_get_config_parameter_bad_parameter_value(config_file) -> None:
    """Test the get_config_parameter help function when bad parameter"""
    parameter_name = "test_parameter"
    with pytest.raises(
        ValueError, match=f"Please fill in {parameter_name} with a value"
    ):
        helper.get_config_parameter(config_file, parameter_name)


# def  test_() -> None:
#     """_summary_"""
