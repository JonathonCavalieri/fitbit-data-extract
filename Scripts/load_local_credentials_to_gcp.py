import sys

sys.path.append("Source/FitbitExtract")
from fitbit.authorization import LocalTokenManager, CloudTokenManager
from helper.functions import get_config_parameter


CONFIG = "config.json"
PROJECT_ID = get_config_parameter(CONFIG, "gcp_project")
BUCKET_NAME_CREDENTIALS = get_config_parameter(CONFIG, "gcp_bucket_credentials")


def transfer_to_gcp():
    token_manager_local = LocalTokenManager()

    token = token_manager_local.load_token()

    gcp_token_manager = CloudTokenManager(
        PROJECT_ID, BUCKET_NAME_CREDENTIALS, token.user_id
    )
    gcp_token_manager.save_token(token)


if __name__ == "__main__":
    transfer_to_gcp()
