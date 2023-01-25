from datetime import datetime
from http import HTTPStatus
import os
import pytest

from fitbit.constants import WEB_API_URL
from fitbit import caller

from tests.fixtures import (  # pylint: disable=W0611
    local_response_saver,
    fitbitcaller,
    api_token,
    local_token_manager,
    api_credentials,
    testing_token_manager,
)


###############################
# Test the FitBitCaller Class #
###############################
def test_register_endpoint(fitbitcaller) -> None:
    """Testing Register Endpoint method of FitBitCaller class"""
    fake_parameters = caller.EndpointParameters("GET", "json")
    endpoint = "get_heart_rate_by_date"
    expected_result = {endpoint: fake_parameters}
    fitbitcaller.register_endpoint(endpoint, fake_parameters)

    assert expected_result == fitbitcaller.registered_endpoints


def test_register_endpoint_not_in_list(fitbitcaller) -> None:
    """Testing Register Endpoint method of FitBitCaller class when endpoint is not in available list"""
    fake_parameters = caller.EndpointParameters(
        "GET", "json", url_kwargs={"parameter1": "value1"}
    )
    endpoint = "fake_endpoint"

    with pytest.raises(ValueError, match=".* not in avaliable list"):
        fitbitcaller.register_endpoint(endpoint, fake_parameters)


def test_refresh_access_token(fitbitcaller, testing_token_manager) -> None:
    """Testing refresh_access_token method of FitBitCaller class"""
    fitbitcaller.refresh_access_token()
    assert fitbitcaller.user_token == testing_token_manager.return_data


def test_register_multiple_endpoints(fitbitcaller) -> None:
    """Testing register_multiple_endpoints method of FitBitCaller class"""
    fake_endpoints = {
        "get_heart_rate_by_date": caller.EndpointParameters("GET", "json"),
        "get_body_weight_by_date": caller.EndpointParameters("GET", "json"),
    }

    fitbitcaller.register_multiple_endpoints(fake_endpoints)

    assert fake_endpoints == fitbitcaller.registered_endpoints


def test_make_registered_requests_for_date_single(tmp_path, fitbitcaller) -> None:
    """Testing make_registered_requests method of FitBitCaller class"""
    fake_parameters = caller.EndpointParameters("GET", "json")
    endpoint = "get_heart_rate_by_date"
    date = datetime.strptime("2023-01-17", "%Y-%m-%d").date()
    data_str = date.strftime("%Y%m%d")
    folder = f"{tmp_path}/{endpoint}/{data_str}"
    file_name = f"{endpoint}_{fitbitcaller.user_token.user_id}"
    expected_file_path = f"{folder}/{file_name}.json"

    fitbitcaller.register_endpoint(endpoint, fake_parameters)
    fitbitcaller.make_registered_requests_for_date(date)

    assert os.path.exists(expected_file_path)


def test_make_registered_requests_for_date_multiple(tmp_path, fitbitcaller) -> None:
    """Testing make_registered_requests method of FitBitCaller class"""
    fake_parameters = {
        "get_heart_rate_by_date": caller.EndpointParameters("GET", "json"),
        "get_body_weight_by_date": caller.EndpointParameters("GET", "json"),
    }
    date = datetime.strptime("2023-01-17", "%Y-%m-%d").date()
    data_str = date.strftime("%Y%m%d")
    fitbitcaller.register_multiple_endpoints(fake_parameters)
    fitbitcaller.make_registered_requests_for_date(date)

    for endpoint, parameters in fake_parameters.items():
        folder = f"{tmp_path}/{endpoint}/{data_str}"
        file_name = f"{endpoint}_{fitbitcaller.user_token.user_id}"
        expected_file_path = f"{folder}/{file_name}.{parameters.response_format}"

        assert os.path.exists(expected_file_path)


def test_make_registered_requests_for_date_unauthorized(tmp_path, fitbitcaller) -> None:
    """Testing make_registered_requests method of FitBitCaller class when Unauthorized"""
    fake_parameters = caller.EndpointParameters("GET", "json")
    endpoint = "get_heart_rate_by_date"
    date = datetime.strptime("2023-01-17", "%Y-%m-%d").date()
    data_str = date.strftime("%Y%m%d")
    folder = f"{tmp_path}/{endpoint}/{data_str}"
    file_name = f"{endpoint}_{fitbitcaller.user_token.user_id}"
    expected_file_path = f"{folder}/{file_name}.json"
    fitbitcaller.requester.http_status = HTTPStatus.UNAUTHORIZED

    fitbitcaller.register_endpoint(endpoint, fake_parameters)
    fitbitcaller.make_registered_requests_for_date(date)

    assert os.path.exists(expected_file_path)


def test_make_registered_requests_for_date_none_registered(fitbitcaller) -> None:
    """Testing make_registered_requests method of FitBitCaller class"""

    date = datetime.strptime("2023-01-17", "%Y-%m-%d").date()
    with pytest.raises(Exception, match="No endpoints have been registered"):
        fitbitcaller.make_registered_requests_for_date(date)


def test_make_registered_requests_for_date_bad_retries(fitbitcaller) -> None:
    """Testing make_registered_requests method of FitBitCaller class"""

    date = datetime.strptime("2023-01-17", "%Y-%m-%d").date()
    fitbitcaller.register_endpoint(
        "get_heart_rate_by_date", caller.EndpointParameters("GET", "json")
    )

    with pytest.raises(ValueError, match="Retries cannot be less than 0"):
        fitbitcaller.make_registered_requests_for_date(date, -1)


def test_make_registered_requests_for_date_too_many_retries(fitbitcaller) -> None:
    """Testing make_registered_requests method of FitBitCaller class"""

    date = datetime.strptime("2023-01-17", "%Y-%m-%d").date()
    fitbitcaller.register_endpoint(
        "get_heart_rate_by_date", caller.EndpointParameters("GET", "json")
    )
    fitbitcaller.requester.http_status = HTTPStatus.BAD_GATEWAY
    fitbitcaller.requester.ok_after = 99
    retries = 6
    with pytest.raises(Exception, match=f"Request failed after {retries} retries"):
        fitbitcaller.make_registered_requests_for_date(date, retries)


##################################################
# Test the FitBitCaller Class create url methods #
##################################################


def test_create_url_heart_rate_default_case(fitbitcaller, api_token) -> None:
    """Testing create_url_heart_rate method of FitBitCaller class with default parameters"""
    date = datetime.strptime("2014-01-04", "%Y-%m-%d").date()
    expected_url = (
        f"{WEB_API_URL}/user/{api_token.user_id}/activities/heart/date/{date}/1d.json"
    )
    url = fitbitcaller.create_url_heart_rate(date)

    assert url == expected_url


def test_create_url_heart_rate(fitbitcaller, api_token) -> None:
    """Testing create_url_heart_rate method of FitBitCaller class with period specified"""
    date = datetime.strptime("2014-01-04", "%Y-%m-%d").date()
    period = "7d"
    expected_url = f"{WEB_API_URL}/user/{api_token.user_id}/activities/heart/date/{date}/{period}.json"
    url = fitbitcaller.create_url_heart_rate(date, period=period)

    assert url == expected_url


def test_create_url_heart_rate_bad_period_value(fitbitcaller) -> None:
    """Testing create_url_heart_rate method of FitBitCaller class when period is not valid"""
    date = datetime.strptime("2014-01-04", "%Y-%m-%d").date()

    with pytest.raises(ValueError, match="Period is not one of the supported values"):
        fitbitcaller.create_url_heart_rate(date, period="2d")


def test_create_url_body_weight(fitbitcaller, api_token) -> None:
    """Testing create_url_body_weight method of FitBitCaller class with default parameters"""
    date = datetime.strptime("2014-01-04", "%Y-%m-%d").date()
    expected_url = (
        f"{WEB_API_URL}/user/{api_token.user_id}/body/log/weight/date/{date}.json"
    )
    url = fitbitcaller.create_url_body_weight(date)

    assert url == expected_url


def test_create_url_activity_summary(fitbitcaller, api_token) -> None:
    """Testing create_url_body_weight method of FitBitCaller class with default parameters"""
    date = datetime.strptime("2014-01-04", "%Y-%m-%d").date()
    expected_url = f"{WEB_API_URL}/user/{api_token.user_id}/activities/date/{date}.json"
    url = fitbitcaller.create_url_activity_summary(date)

    assert url == expected_url
