from tests.fixtures import messenger
from fitbit.caller import EndpointParameters

################################
# Testing LocalMessenger Class #
################################
def test_local_prep_message(messenger) -> None:
    """test the prep_message method from LocalMessenger class"""
    endpoints = [EndpointParameters("test1"), EndpointParameters("test2")]
    user_id = "TESTUSER"
    date = "2023-01-18"

    messages = messenger.prep_message(endpoints, user_id, date)

    expected_message = b'{"user_id": "TESTUSER", "date": "2023-01-18", "endpoints": [{"name": "test1", "method": "GET", "response_format": "json", "url_kwargs": {}, "body": {}, "headers": {}}, {"name": "test2", "method": "GET", "response_format": "json", "url_kwargs": {}, "body": {}, "headers": {}}]}'

    assert messages == expected_message


def test_local_prep_message_no_data(messenger) -> None:
    """test the prep_message method from LocalMessenger class when no data is provided"""
    user_id = "TESTUSER"
    date = "2023-01-18"
    endpoints = []
    messages = messenger.prep_message(endpoints, user_id, date)
    assert messages is None


def test_local_send_message(messenger, capsys) -> None:
    """ "test the send_message method from LocalMessenger class"""
    endpoints = [EndpointParameters("test1"), EndpointParameters("test2")]
    user_id = "TESTUSER"
    date = "2023-01-18"
    messages = messenger.prep_message(endpoints, user_id, date)
    response = messenger.send_message(messages)
    captured = capsys.readouterr()
    expected_value = """sending message: b'{"user_id": "TESTUSER", "date": "2023-01-18", "endpoints": [{"name": "test1", "method": "GET", "response_format": "json", "url_kwargs": {}, "body": {}, "headers": {}}, {"name": "test2", "method": "GET", "response_format": "json", "url_kwargs": {}, "body": {}, "headers": {}}]}'
"""
    assert captured.out == expected_value
    assert response == "success"


def test_local_prep_message_all(messenger) -> None:
    """test the prep_message method from LocalMessenger class"""
    endpoints = ["all"]
    user_id = "TESTUSER"
    date = "2023-01-18"

    messages = messenger.prep_message(endpoints, user_id, date)

    expected_message = (
        b'{"user_id": "TESTUSER", "date": "2023-01-18", "endpoints": ["all"]}'
    )

    assert messages == expected_message
