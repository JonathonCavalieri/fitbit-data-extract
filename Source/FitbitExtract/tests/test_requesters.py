import pytest
from tests.fixtures import requester  # pylint: disable=W0611


def test_make_request_get(requester) -> None:
    test_message = '{"test_key": "test_value"}\n'
    test_url = "http://echo.jsontest.com/test_key/test_value"
    message, code = requester.make_request("GET", test_url, {}, {})

    assert message == test_message
    assert code == 200


def test_make_request_bad_method(requester) -> None:
    with pytest.raises(ValueError, match="Invalid method"):
        requester.make_request("BD_METHOD", "", {}, {})


def test_make_request_bad_status(capsys, requester) -> None:

    test_url = "https://httpstat.us/403"
    message, code = requester.make_request("GET", test_url, {}, {})
    captured = capsys.readouterr()
    assert message == "403 Forbidden"
    assert code == 403
    assert "https://httpstat.us/403 403 403 Forbidden\n" == captured.out
