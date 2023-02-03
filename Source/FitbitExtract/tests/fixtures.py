from http import HTTPStatus
from datetime import datetime
import json
import os
import pytest


from fitbit import authorization as auth
from fitbit import caller, savers, requesters, loaders, messengers, transformers


############################################
# Ceate a testing requester to simulate API #
############################################
class TestingFitbitRequester:
    """A test requester object used for testing"""

    def __init__(self) -> None:
        self.response = '{"field1": "value1", "field2": 2, "field3": "value3"}'
        self.http_status = HTTPStatus.OK
        self.called = 0
        self.ok_after = 1

    def make_request(  # pylint: disable=W0613
        self, method: str, url: str, headers: dict, body: dict
    ) -> tuple[str, HTTPStatus]:
        """
        simulates make requests method, this will revert to  http status OK after being called X
        times specified in setup if set to another status
        """
        self.called += 1
        if self.called > self.ok_after:
            self.http_status = HTTPStatus.OK

        return self.response, self.http_status


class TestingTokenManager:
    """
    A fake token manager used for testings
    """

    def __init__(
        self, token: auth.FitbitToken, credentials: auth.FitbitAppCredentials
    ) -> None:
        self.return_data = token
        self.credentials = credentials
        self.return_data.access_token_isvalid = True

    def refresh_token(  # pylint: disable=W0613
        self, token: auth.FitbitToken
    ) -> auth.FitbitToken:
        """Refreshes a fitbit access token"""
        return self.return_data

    def load_credentials(self) -> None:
        """Load Credentials from storage"""

    def load_token(self) -> auth.FitbitToken:  # pylint: disable=W0613
        """Load API Token from storage"""
        return self.return_data

    def save_token(self, token: auth.FitbitToken) -> None:
        """Save API Token to storage"""


############################################
# Create fixture objects to use in testing #
############################################
@pytest.fixture()
def api_token() -> auth.FitbitToken:
    """fixture for api token for testing

    Returns:
        FitbitToken: test api token object
    """
    return auth.FitbitToken(
        "test_refresh_token", "test_access_token", "test_scope", "test_user"
    )


@pytest.fixture()
def api_credentials() -> auth.FitbitAppCredentials:
    """Pytest fixture for api credentials for testing

    Returns:
        FitbitAppCredentials: test api credentials object
    """
    return auth.FitbitAppCredentials("test_client_id", "test_client_secret")


@pytest.fixture()
def local_token_manager(tmp_path, api_credentials) -> auth.TokenManager:
    """Pytest fixture for a token manager for testing

    Returns:
        TokenManager: an instance of a token manager used for testing
    """
    manager_parameters = auth.LocalTokenManagerParameters(
        credentials_directory=f"{tmp_path}/credentials",
        credentials_name="test_save_local_credentials",
        token_directory=f"{tmp_path}/tokens",
        token_name="test_save_local_token",
        load_credentials=False,
    )

    return auth.LocalTokenManager(
        parameters=manager_parameters,
        credentials=api_credentials,
    )


@pytest.fixture()
def testing_token_manager(api_credentials) -> auth.TokenManager:
    """
    A Testing token manager to simulate functionality in other objects
    """
    refreshed_token = auth.FitbitToken(
        "refreshed", "test_access_token", "test_scope", "test_user"
    )
    return TestingTokenManager(refreshed_token, api_credentials)


@pytest.fixture()
def local_response_saver(tmp_path) -> caller.FitbitResponseSaver:
    """
    A testing local repsonse saver using the tmp_path
    """
    base_directory = tmp_path

    return savers.LocalResponseSaver(base_directory)


@pytest.fixture()
def fitbitcaller(
    api_token, local_response_saver, testing_token_manager
) -> caller.FitBitCaller:
    """Pytest fixture for a token manager for testing

    Returns:
        TokenManager: an instance of a token manager used for testing
    """
    requester = TestingFitbitRequester()

    return caller.FitBitCaller(
        api_token, local_response_saver, requester, testing_token_manager
    )


@pytest.fixture()
def requester() -> requesters.WebAPIRequester:
    """Requester fixture for testing"""
    return requesters.WebAPIRequester()


@pytest.fixture()
def loader() -> loaders.LocalDataLoader:
    """Local Data Loader for Testing"""
    return loaders.LocalDataLoader()


@pytest.fixture()
def messenger() -> messengers.LocalMessenger:
    """Local Messenger fixture for Testing"""
    return messengers.LocalMessenger()


@pytest.fixture()
def transformer(loader, messenger) -> transformers.FitbitETL:
    """FitBit ETL transformer fixture for Testing"""

    a_transformer = transformers.FitbitETL(loader, messenger)
    # Overide the processing time with a static value
    a_transformer.processing_datetime = "2023-02-03 12:31:38"
    return a_transformer


#####################################
# Create files for testing purposes #
#####################################


@pytest.fixture()
def config_file():
    return "Source/FitbitExtract/tests/testing_data_files/test_config/test_config.json"


@pytest.fixture(scope="session")
def session_temp(tmp_path_factory):
    """Global session temp path for data"""
    path = tmp_path_factory.mktemp("temp_data")
    path = os.path.join(path, "20230118")
    os.mkdir(path)
    return path


@pytest.fixture(scope="session")
def test_data_path(session_temp) -> tuple[str, dict]:
    data = {"cardioScore": [{"dateTime": "2023-01-18", "value": {"vo2Max": "44-48"}}]}
    path = f"{session_temp}/get_cardio_score_by_date_TESTUSER.json"
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

    return (path, data)


@pytest.fixture(scope="session")
def test_data_path_tcx(session_temp) -> tuple[str, dict]:
    """testing file for xml data"""

    data = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <TrainingCenterDatabase xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2">
        <Activities>
            <Activity Sport="Running">
                <Id>2022-10-13T07:07:03.000+11:00</Id>
                <Lap StartTime="2022-10-13T07:07:03.000+11:00">
                    <TotalTimeSeconds>414.0</TotalTimeSeconds>
                    <DistanceMeters>1000.0</DistanceMeters>
                    <Calories>67</Calories>
                    <Intensity>Active</Intensity>
                    <TriggerMethod>Manual</TriggerMethod>
                    <Track>
                        <Trackpoint>
                            <Time>2022-10-13T07:07:03.000+11:00</Time>
                            <Position>
                                <LatitudeDegrees>-33.89690887928009</LatitudeDegrees>
                                <LongitudeDegrees>151.19783425331116</LongitudeDegrees>
                            </Position>
                            <AltitudeMeters>44.48640000833932</AltitudeMeters>
                            <DistanceMeters>0.0</DistanceMeters>
                            <HeartRateBpm>
                                <Value>90</Value>
                            </HeartRateBpm>
                        </Trackpoint>
                    </Track>
                </Lap>
                <Creator xsi:type="Device_t" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <UnitId>0</UnitId>
                    <ProductID>0</ProductID>
                </Creator>
            </Activity>
        </Activities>
    </TrainingCenterDatabase>
    """

    path = f"{session_temp}/activities.tcx"
    with open(path, "w", encoding="utf-8") as file:
        file.write(data)

    return (path, data)


#####################################
# Create files for testing purposes #
#####################################


@pytest.fixture(scope="session")
def testing_data_dictionarys() -> dict:
    test_files_directory = "Source/FitbitExtract/tests/testing_data_files/endpoint_data"
    transformer = transformers.FitbitETL(loaders.LocalDataLoader(), None)
    out_dict = {}
    for root, _, files in os.walk(test_files_directory):
        for file in files:
            file_path = os.path.join(root, file)
            transformer.get_details_from_path(file_path)
            data = transformer.extract_data()
            temp_dict = {
                "data": data,
                "user_id": transformer.user_id,
                "date": transformer.date,
            }
            if transformer.instance_id:
                temp_dict["instance_id"] = transformer.instance_id

            out_dict[transformer.endpoint] = temp_dict

    return out_dict
