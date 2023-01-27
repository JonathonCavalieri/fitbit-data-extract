import pytest
import base64
import json
from datetime import date, timedelta, datetime

from fitbit.caller import EndpointParameters
import main


def test_decode_event_messages() -> None:
    """_summary_"""
    test_message = {"test_key": "test_value"}
    test_message_encoded = json.dumps(test_message).encode("utf-8")
    test_message_data = {"message": {"data": base64.b64encode(test_message_encoded)}}
    assert test_message == main.decode_event_messages(test_message_data)


def test_decode_event_messages_bad_dict() -> None:
    """_summary_"""
    test_message = b"This is a bad message"
    test_message_data = {"message": {"data": base64.b64encode(test_message)}}

    with pytest.raises(
        Exception, match="Could not parse pubsub message: .* into a dict"
    ):
        main.decode_event_messages(test_message_data)


def test_check_parameters_date() -> None:
    """_summary_"""
    parameters = {"user_id": "test", "endpoints": "test"}
    with pytest.raises(KeyError, match="date was not provided in message body"):
        main.check_parameters(parameters)


def test_check_parameters_user_id() -> None:
    """_summary_"""
    parameters = {"date": "test", "endpoints": "test"}
    with pytest.raises(KeyError, match="user_id was not provided in message body"):
        main.check_parameters(parameters)


def test_check_parameters_endpoints() -> None:
    """_summary_"""
    parameters = {"user_id": "test", "date": "test"}
    with pytest.raises(KeyError, match="endpoints was not provided in message body"):
        main.check_parameters(parameters)


def test_get_date_current() -> None:
    """_summary_"""
    parameters = {"date": "current"}
    expected_date = date.today() - timedelta(days=1)

    assert expected_date == main.get_date(parameters)


def test_get_date() -> None:
    """_summary_"""
    parameters = {"date": "2022-03-03"}
    expected_date = datetime.strptime(parameters["date"], "%Y-%m-%d").date()

    assert expected_date == main.get_date(parameters)


def test_get_endpoints_not_list() -> None:
    """_summary_"""
    parameters = {"endpoints": "test"}
    with pytest.raises(
        ValueError, match="Endpoints should be passed as a list even for a single value"
    ):
        main.get_endpoints(parameters)


def test_get_endpoints_all() -> None:
    """_summary_"""
    parameters = {"endpoints": ["all"]}

    assert main.ENDPOINTS == main.get_endpoints(parameters)


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

    assert expected_result == main.get_endpoints(parameters)


# def  test_() -> None:
#     """_summary_"""
