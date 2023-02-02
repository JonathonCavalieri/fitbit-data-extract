import webbrowser

from fitbit.authorization import FitbitToken, LocalTokenManager, CloudTokenManager
from fitbit.local_authorization import (
    generate_authorization_request,
    generate_code_verifier,
    parse_return_url,
    get_access_token,
)
from helper.functions import get_config_parameter


CONFIG = "config.json"
PROJECT_ID = get_config_parameter(CONFIG, "gcp_project")
BUCKET_NAME_CREDENTIALS = get_config_parameter(CONFIG, "gcp_bucket_credentials")


def main() -> None:
    client_id = input("Enter Client Id: ")
    client_secret = input("Enter Client Secret: ")
    scopes = input("Enter Scopes: ")
    code_verifier = generate_code_verifier()
    auth_url = generate_authorization_request(client_id, scopes, code_verifier)
    webbrowser.open(auth_url, new=0, autoraise=True)
    returned_url = input("Paste response from callback: ")
    authorization_code = parse_return_url(returned_url)

    token = get_access_token(
        client_id, client_secret, code_verifier, authorization_code
    )

    fitbit_token = FitbitToken(
        token["refresh_token"],
        token["access_token"],
        token["scope"],
        token["user_id"],
        access_token_isvalid=True,
    )
    # token_manager = LocalTokenManager()
    token_manager = CloudTokenManager(
        PROJECT_ID, BUCKET_NAME_CREDENTIALS, fitbit_token.user_id
    )
    token_manager.save_token(fitbit_token)


if __name__ == "__main__":
    main()
