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
    fake_endpoint = caller.EndpointParameters("get_heart_rate_by_date", "GET", "json")
    expected_result = [fake_endpoint]
    fitbitcaller.register_endpoint(fake_endpoint)

    assert expected_result == fitbitcaller.registered_endpoints


def test_register_endpoint_not_in_list(fitbitcaller) -> None:
    """Testing Register Endpoint method of FitBitCaller class when endpoint is not in available list"""
    fake_endpoint = caller.EndpointParameters(
        "fake_endpoint", "GET", "json", url_kwargs={"parameter1": "value1"}
    )

    with pytest.raises(ValueError, match=".* not in avaliable list"):
        fitbitcaller.register_endpoint(fake_endpoint)


def test_refresh_access_token(fitbitcaller, testing_token_manager) -> None:
    """Testing refresh_access_token method of FitBitCaller class"""
    fitbitcaller.refresh_access_token()
    assert fitbitcaller.user_token == testing_token_manager.return_data


def test_register_multiple_endpoints(fitbitcaller) -> None:
    """Testing register_multiple_endpoints method of FitBitCaller class"""
    fake_endpoints = [
        caller.EndpointParameters("get_heart_rate_by_date", "GET", "json"),
        caller.EndpointParameters("get_body_weight_by_date", "GET", "json"),
    ]

    fitbitcaller.register_multiple_endpoints(fake_endpoints)

    assert fake_endpoints == fitbitcaller.registered_endpoints


def test_make_registered_requests_for_date_single(tmp_path, fitbitcaller) -> None:
    """Testing make_registered_requests method of FitBitCaller class"""
    endpoint = caller.EndpointParameters("get_heart_rate_by_date", "GET", "json")

    date = datetime.strptime("2023-01-17", "%Y-%m-%d").date()
    data_str = date.strftime("%Y%m%d")
    folder = f"{tmp_path}/{endpoint.name}/{data_str}"

    url_func = fitbitcaller.available_endpoints[endpoint.name]
    _, instance_name = url_func(date, **endpoint.url_kwargs)

    file_name = f"{instance_name}_{fitbitcaller.user_token.user_id}"
    expected_file_path = f"{folder}/{file_name}.json"

    fitbitcaller.register_endpoint(endpoint)
    fitbitcaller.make_registered_requests_for_date(date)

    assert os.path.exists(expected_file_path)


def test_make_registered_requests_for_date_multiple(tmp_path, fitbitcaller) -> None:
    """Testing make_registered_requests method of FitBitCaller class"""
    endpoints = [
        caller.EndpointParameters("get_heart_rate_by_date", "GET", "json"),
        caller.EndpointParameters("get_body_weight_by_date", "GET", "json"),
    ]

    date = datetime.strptime("2023-01-17", "%Y-%m-%d").date()
    data_str = date.strftime("%Y%m%d")
    fitbitcaller.register_multiple_endpoints(endpoints)
    fitbitcaller.make_registered_requests_for_date(date)

    for endpoint in endpoints:

        url_func = fitbitcaller.available_endpoints[endpoint.name]

        _, instance_name = url_func(date, **endpoint.url_kwargs)

        folder = f"{tmp_path}/{endpoint.name}/{data_str}"
        file_name = f"{instance_name}_{fitbitcaller.user_token.user_id}"
        expected_file_path = f"{folder}/{file_name}.{endpoint.response_format}"

        assert os.path.exists(expected_file_path)


def test_make_registered_requests_for_date_unauthorized(tmp_path, fitbitcaller) -> None:
    """Testing make_registered_requests method of FitBitCaller class when Unauthorized"""
    endpoint = caller.EndpointParameters("get_heart_rate_by_date", "GET", "json")

    date = datetime.strptime("2023-01-17", "%Y-%m-%d").date()
    data_str = date.strftime("%Y%m%d")
    folder = f"{tmp_path}/{endpoint.name}/{data_str}"
    url_func = fitbitcaller.available_endpoints[endpoint.name]
    _, instance_name = url_func(date, **endpoint.url_kwargs)

    file_name = f"{instance_name}_{fitbitcaller.user_token.user_id}"
    expected_file_path = f"{folder}/{file_name}.json"
    fitbitcaller.requester.http_status = HTTPStatus.UNAUTHORIZED

    fitbitcaller.register_endpoint(endpoint)
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
        caller.EndpointParameters("get_heart_rate_by_date", "GET", "json")
    )

    with pytest.raises(ValueError, match="Retries cannot be less than 0"):
        fitbitcaller.make_registered_requests_for_date(date, -1)


def test_make_registered_requests_for_date_too_many_retries(fitbitcaller) -> None:
    """Testing make_registered_requests method of FitBitCaller class"""

    date = datetime.strptime("2023-01-17", "%Y-%m-%d").date()
    fitbitcaller.register_endpoint(
        caller.EndpointParameters("get_heart_rate_by_date", "GET", "json")
    )
    fitbitcaller.requester.http_status = HTTPStatus.BAD_GATEWAY
    fitbitcaller.requester.ok_after = 99
    retries = 6
    with pytest.raises(Exception, match=f"Request failed after {retries} retries"):
        fitbitcaller.make_registered_requests_for_date(date, retries)


def test_make_registered_requests_for_date_forbidden(fitbitcaller) -> None:
    """Testing make_registered_requests method of FitBitCaller class"""

    date = datetime.strptime("2023-01-17", "%Y-%m-%d").date()
    fitbitcaller.register_endpoint(
        caller.EndpointParameters("get_heart_rate_by_date", "GET", "json")
    )
    fitbitcaller.requester.http_status = HTTPStatus.FORBIDDEN
    fitbitcaller.requester.ok_after = 99
    with pytest.raises(Exception, match="Request is forbidden please check user scope"):
        fitbitcaller.make_registered_requests_for_date(date)


##################################################
# Test the FitBitCaller Class create url methods #
##################################################


def test_create_url_heart_rate_default_case(fitbitcaller, api_token) -> None:
    """Testing create_url_heart_rate method of FitBitCaller class with default parameters"""
    date = datetime.strptime("2014-01-04", "%Y-%m-%d").date()
    expected_url = (
        f"{WEB_API_URL}/1/user/{api_token.user_id}/activities/heart/date/{date}/1d.json"
    )
    url, save_name = fitbitcaller.create_url_heart_rate(date)

    assert url == expected_url
    assert save_name == "get_heart_rate_by_date"


def test_create_url_heart_rate(fitbitcaller, api_token) -> None:
    """Testing create_url_heart_rate method of FitBitCaller class with period specified"""
    date = datetime.strptime("2014-01-04", "%Y-%m-%d").date()
    period = "7d"
    expected_url = f"{WEB_API_URL}/1/user/{api_token.user_id}/activities/heart/date/{date}/{period}.json"
    url, save_name = fitbitcaller.create_url_heart_rate(date, period=period)

    assert url == expected_url
    assert save_name == "get_heart_rate_by_date"


def test_create_url_heart_rate_bad_period_value(fitbitcaller) -> None:
    """Testing create_url_heart_rate method of FitBitCaller class when period is not valid"""
    date = datetime.strptime("2014-01-04", "%Y-%m-%d").date()

    with pytest.raises(ValueError, match="Period is not one of the supported values"):
        fitbitcaller.create_url_heart_rate(date, period="2d")


def test_create_url_body_weight(fitbitcaller, api_token) -> None:
    """Testing create_url_body_weight method of FitBitCaller class with default parameters"""
    date = datetime.strptime("2014-01-04", "%Y-%m-%d").date()
    expected_url = (
        f"{WEB_API_URL}/1/user/{api_token.user_id}/body/log/weight/date/{date}.json"
    )
    url, save_name = fitbitcaller.create_url_body_weight(date)

    assert url == expected_url
    assert save_name == "get_body_weight_by_date"


def test_create_url_activity_summary(fitbitcaller, api_token) -> None:
    """Testing create_url_body_weight method of FitBitCaller class with default parameters"""
    date = datetime.strptime("2014-01-04", "%Y-%m-%d").date()
    expected_url = (
        f"{WEB_API_URL}/1/user/{api_token.user_id}/activities/date/{date}.json"
    )
    url, save_name = fitbitcaller.create_url_activity_summary(date)

    assert url == expected_url
    assert save_name == "get_activity_summary_by_date"


def test_create_url_activity_tcx(fitbitcaller, api_token) -> None:
    """Testing create_url_activity_tcx method of FitBitCaller class with default parameters"""
    date = datetime.strptime("2014-01-04", "%Y-%m-%d").date()
    log_id = "test"
    expected_url = f"{WEB_API_URL}/1/user/{api_token.user_id}/activities/{log_id}.tcx?includePartialTCX=true"

    url, save_name = fitbitcaller.create_url_activity_tcx(date, log_id=log_id)

    assert url == expected_url
    assert save_name == f"{log_id}_get_activity_tcx_by_id"


def test_create_url_activity_tcx_no_partialtcx(fitbitcaller, api_token) -> None:
    """Testing create_url_activity_tcx method of FitBitCaller class with no partial tcx parameter"""
    date = datetime.strptime("2014-01-04", "%Y-%m-%d").date()
    log_id = "test"
    expected_url = f"{WEB_API_URL}/1/user/{api_token.user_id}/activities/{log_id}.tcx?includePartialTCX=false"

    url, save_name = fitbitcaller.create_url_activity_tcx(
        date, log_id=log_id, partialtcx=False
    )

    assert url == expected_url
    assert save_name == f"{log_id}_get_activity_tcx_by_id"


def test_create_url_activity_tcx_no_logid(fitbitcaller) -> None:
    """Testing create_url_activity_tcx method of FitBitCaller class when no log_id is provided"""
    date = datetime.strptime("2014-01-04", "%Y-%m-%d").date()

    with pytest.raises(ValueError, match="log_id was not provided as a parameter"):
        fitbitcaller.create_url_activity_tcx(date)


def test_create_url_activity_details(fitbitcaller, api_token) -> None:
    """Testing create_url_activity_details method of FitBitCaller class with default parameters"""
    log_id = "test"
    date = datetime.strptime("2014-01-04", "%Y-%m-%d").date()
    expected_url = f"{WEB_API_URL}/1/user/{api_token.user_id}/activities/{log_id}.json"

    url, save_name = fitbitcaller.create_url_activity_details(date, log_id=log_id)
    assert url == expected_url
    assert save_name == f"{log_id}_get_activity_details_by_id"


def test_create_url_activity_details_no_log_id(fitbitcaller) -> None:
    """Testing create_url_activity_details method of FitBitCaller class when no log id is provided"""
    date = datetime.strptime("2014-01-04", "%Y-%m-%d").date()

    with pytest.raises(ValueError, match="log_id was not provided as a parameter"):
        fitbitcaller.create_url_activity_details(date)


def test_create_url_heart_rate_variablity(fitbitcaller, api_token) -> None:
    """Testing create_url_heart_rate_variablity method of FitBitCaller class with default parameters"""
    date = datetime.strptime("2014-01-04", "%Y-%m-%d").date()
    expected_url = f"{WEB_API_URL}/1/user/{api_token.user_id}/hrv/date/{date}/all.json"
    url, save_name = fitbitcaller.create_url_heart_rate_variablity(date)

    assert url == expected_url
    assert save_name == "get_heart_rate_variablity_by_date"


def test_create_url_cardio_score(fitbitcaller, api_token) -> None:
    """Testing create_url_cardio_score method of FitBitCaller class with default parameters"""
    date = datetime.strptime("2014-01-04", "%Y-%m-%d").date()
    expected_url = (
        f"{WEB_API_URL}/1/user/{api_token.user_id}/cardioscore/date/{date}.json"
    )
    url, save_name = fitbitcaller.create_url_cardio_score(date)

    assert url == expected_url
    assert save_name == "get_cardio_score_by_date"


def test_create_url_sleep(fitbitcaller, api_token) -> None:
    """Testing create_url_sleep method of FitBitCaller class with default parameters"""
    date = datetime.strptime("2014-01-04", "%Y-%m-%d").date()
    expected_url = f"{WEB_API_URL}/1.2/user/{api_token.user_id}/sleep/date/{date}.json"
    url, save_name = fitbitcaller.create_url_sleep(date)

    assert url == expected_url
    assert save_name == "get_sleep_by_date"
