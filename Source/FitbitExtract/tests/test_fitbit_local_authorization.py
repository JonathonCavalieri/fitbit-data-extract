import re
from string import ascii_letters, digits
from http import HTTPStatus
from requests.exceptions import HTTPError
import fitbit.local_authorization as auth
import pytest
from fitbit.constants import POSSIBLE_SCOPES, TOKEN_URL


def test_generate_code_challenge() -> None:
    """
    Test the code challenge function to ensure it returns expected result
    """

    code_verifier = "01234567890123456789012345678901234567890123456789"
    code_challenge, challenge_method = auth.generate_code_challenge(code_verifier)
    assert (
        code_challenge == b"-4cf-Mzo_qg9-uq0F4QwWhRh4AjcAqNx7SbYVsdmyQM"
        and challenge_method == "S256"
    )


def test_generate_code_verifier() -> None:
    """
    Test the code verifier function to ensure it returns expected result
    """

    possible_chars = digits + ascii_letters
    code_verifier = auth.generate_code_verifier()

    character_check = set(code_verifier).issubset(set(possible_chars))
    length_check = len(code_verifier) >= 43 and len(code_verifier) <= 128
    assert length_check and character_check


def test_generate_authorization_request_scopes() -> None:
    """
    Test the generate_authorization_request function to ensure it the check for correct scopes works
    """

    client_id = "test_id"
    scopes = "activity weight badscope"
    code_verifier = "testing"
    error_string = re.escape(
        f"One of the scopes is not in possible list. Must be one of: {POSSIBLE_SCOPES}"
    )
    with pytest.raises(ValueError, match=error_string):
        auth.generate_authorization_request(client_id, scopes, code_verifier)


def test_generate_authorization_request() -> None:
    """
    Test the generate_authorization_request function to check that it returns the correct url
    """

    client_id = "test_id"
    scopes = "activity weight"
    code_verifier = (
        "1QEOx86YURY4yiuVZpRw5h1KomsJrKoupkoDQHfXuUt8GgtMrlLaPGmKYfo44mG6Odb64M1P"
    )
    expected_url = "https://www.fitbit.com/oauth2/authorize?client_id=test_id&scope=activity+weight&code_challenge=qlaG6l2FKLYo0o1o9YBmLbyfeGneVvytHc8lyvI4sIY&code_challenge_method=S256&response_type=code"
    assert (
        auth.generate_authorization_request(client_id, scopes, code_verifier)
        == expected_url
    )


def test_parse_return_url() -> None:
    """
    Test the parse_return_url function to check that it returns the token when provide by a valid url
    """
    token = "10abee9328167561bdcf92ffb8cf23e06620248a"
    url = f"http://127.0.0.1:8080/?code={token}#_=_"

    assert token == auth.parse_return_url(url)


def test_parse_return_url_bad_url() -> None:
    """
    Test the parse_return_url function to check that it returns the token when provide by a invalid url
    """
    token = "10abee9328167561bdcf92ffb8cf23e06620248a"
    url = f"http://127.0.0.1:8080/?code{token}#_=_"

    with pytest.raises(ValueError, match="Could not parse token from provided url"):
        auth.parse_return_url(url)


def test_get_access_token(requests_mock) -> None:
    """
    Test the get_access_token function to check that it returns a response for http OK
    """
    requests_mock.post(
        TOKEN_URL,
        json={"access_token": "test_access_token"},
        status_code=HTTPStatus.OK,
    )

    access_token = auth.get_access_token(
        "test_id", "test_secret", "test_verifier", "test_code"
    )

    assert access_token == {"access_token": "test_access_token"}


def test_get_access_token_no_client_id() -> None:
    """
    Test the get_access_token function to check missing client id case is handled
    """

    with pytest.raises(ValueError, match="Client id must be filled in"):
        auth.get_access_token("", "test_secret", "test_verifier", "test_code")

    with pytest.raises(ValueError, match="Client id must be filled in"):
        auth.get_access_token(None, "test_secret", "test_verifier", "test_code")


def test_get_access_token_no_client_secret() -> None:
    """
    Test the get_access_token function to check missing client secret case is handled
    """

    with pytest.raises(ValueError, match="Client secret must be filled in"):
        auth.get_access_token("test_id", "", "test_verifier", "test_code")

    with pytest.raises(ValueError, match="Client secret must be filled in"):
        auth.get_access_token("test_id", None, "test_verifier", "test_code")


def test_get_access_token_bad_status(requests_mock) -> None:
    """
    Test the get_access_token function to check that it returns a response for when http status is no OK
    """
    requests_mock.post(
        TOKEN_URL,
        json={"access_token": "test_access_token"},
        status_code=HTTPStatus.BAD_GATEWAY,
    )

    with pytest.raises(HTTPError):
        auth.get_access_token("test_id", "test_secret", "test_verifier", "test_code")
