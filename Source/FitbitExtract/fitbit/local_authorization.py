from hashlib import sha256
from base64 import urlsafe_b64encode
from random import choice, randint
from string import digits, ascii_letters
from urllib.parse import urlencode
import re

# installed packages
import requests

# local dependencies
from fitbit.constants import POSSIBLE_SCOPES, AUTHORIZATION_URL, TOKEN_URL


def generate_code_verifier() -> str:
    """Generates a random set of alphanumeric characters with a length between 43-128

    Returns:
        str: code verifier string
    """
    length = randint(43, 128)
    possible_chars = digits + ascii_letters
    return "".join(choice(possible_chars) for _ in range(length))


def generate_code_challenge(code_verifier: str) -> tuple:
    """Transforms the code_verifier into a code challenge
    by hashing the string then base64 urls encoding omitting the final =

    Args:
        code_verifier (str): Code verifier string

    Returns:
        str: code challenge string
        str: code challenge method
    """
    hashed_code = sha256(code_verifier.encode("utf-8"))
    code_challenge_string = urlsafe_b64encode(hashed_code.digest())
    return code_challenge_string[:-1], "S256"


def generate_authorization_request(
    client_id: str, scope: str, code_verifier: str
) -> str:
    """_summary_

    Args:
        client_id (str): application client id
        scope (str): scopes that application will use. Should be space seperate list
        code_verifier (str): 43-128 random alphanumeric string

    Raises:
        ValueError: Scopes not in possible list of values

    Returns:
        str: Urls to be used by the user to login in fitbit and generate auth code
    """
    code_challenge, challenge_method = generate_code_challenge(code_verifier)

    # check the scopes
    if not set(scope.split()).issubset(set(POSSIBLE_SCOPES)):
        raise ValueError(
            f"One of the scopes is not in possible list. Must be one of: {POSSIBLE_SCOPES}"
        )

    query_params = {
        "client_id": client_id,
        "scope": scope,
        "code_challenge": code_challenge,
        "code_challenge_method": challenge_method,
        "response_type": "code",
    }

    query_params = urlencode(query_params)

    return f"{AUTHORIZATION_URL}?{query_params}"


def parse_return_url(returned_url: str) -> str:
    """Extracts the authorization token out of the urls provided

    Args:
        returned_url (str): URL provided in the callback of authorization process

    Raises:
        ValueError: If token cannot be extract from url because it doesnt match expected pattern

    Returns:
        str: Authorization code
    """
    token_search = re.search(".*=(.*?)#_=_", returned_url, re.IGNORECASE)

    if token_search is None:
        raise ValueError("Could not parse token from provided url")

    return token_search.group(1)


def get_access_token(
    client_id: str, client_secret: str, code_verifier: str, authorization_code: str
) -> str:
    """_summary_

    Args:
        client_id (str): application client id
        client_secret (str): application client secret
        scope (str): scopes that application will use. Should be space seperate list
        code_verifier (str): 43-128 random alphanumeric string


    Returns:
        str: access and refresh token in json format
    """
    if client_id is None or not client_id:
        raise ValueError("Client id must be filled in")

    if client_secret is None or not client_secret:
        raise ValueError("Client secret must be filled in")

    body = {
        "client_id": client_id,
        "code": authorization_code,
        "code_verifier": code_verifier,
        "grant_type": "authorization_code",
    }
    headers = {"Content-type": "application/x-www-form-urlencoded"}
    response = requests.post(
        TOKEN_URL,
        headers=headers,
        data=body,
        timeout=600,
        auth=(client_id, client_secret),
    )

    response.raise_for_status()
    return response.json()
