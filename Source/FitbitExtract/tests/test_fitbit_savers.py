import pytest
import os

from tests.fixtures import (  # pylint: disable=W0611
    local_response_saver,
    gcp_response_saver,
    gcp_storage_client,
)


#####################################
# Test the LocalResponseSaver Class #
#####################################
def test_local_response_saver_json(tmp_path, local_response_saver) -> None:
    """Test the local save object with saving a json file"""
    fake_json_data = '{"field1": "value1", "field2": 2, "field3": "value3"}'
    folder = "data"
    file_format = "json"
    file_name = "test_save_file"
    directory = f"{tmp_path}/{folder}"
    full_path = f"{directory}/{file_name}.{file_format}"

    local_response_saver.save(fake_json_data, folder, file_name, file_format)

    assert os.path.exists(full_path)

    with open(full_path, "r", encoding="utf-8") as file:
        saved_data = file.read()

    assert saved_data == fake_json_data


def test_local_response_saver_xml(tmp_path, local_response_saver) -> None:
    """Test the local save object with saving a xml file"""
    fake_xml_data = """
        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <trainingcenterdatabase xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2">
            <activities>
                <activity sport="Other">
                    <id>2020-01-01T14:59:42.000-07:00</id>
                    <lap starttime="2020-04-01T14:59:42.000-07:00">
                        <totaltimeseconds>1077.0</totaltimeseconds>
                        <distancemeters>1585.9</distancemeters>
                        <calories>221</calories>
                    </lap>
                </activity>
            </activities>
        </trainingcenterdatabase>
        """
    folder = "data"
    file_format = "xml"
    file_name = "test_save_file"
    directory = f"{tmp_path}/{folder}"
    full_path = f"{directory}/{file_name}.{file_format}"

    local_response_saver.save(fake_xml_data, folder, file_name, file_format)

    assert os.path.exists(full_path)

    with open(full_path, "r", encoding="utf-8") as file:
        saved_data = file.read()

    assert saved_data == fake_xml_data


def test_local_response_saver_bad_directory(local_response_saver) -> None:
    """Test the local save object with saving a json file"""
    fake_json_data = '{"field1": "value1", "field2": 2, "field3": "value3"}'
    folder = "data"
    file_format = "json"
    file_name = "test_save_file"

    local_response_saver.make_directory = False

    with pytest.raises(
        FileNotFoundError, match="\\[Errno 2\\] No such file or directory:.*"
    ):
        local_response_saver.save(fake_json_data, folder, file_name, file_format)


###################################
# Test the GCPResponseSaver Class #
###################################


# def test_gcp_response_saver_json(gcp_response_saver) -> None:
#     """Test the GCP save object with saving a json file"""
#     fake_json_data = '{"field1": "value1", "field2": 2, "field3": "value3"}'
#     folder = "data"
#     file_format = "json"
#     file_name = "test_save_file"

#     gcp_response_saver.save(fake_json_data, folder, file_name, file_format)
#     blob_name = f"{folder}/{file_name}.{file_format}"
#     blob = gcp_response_saver.bucket.blob(blob_name)

#     assert blob.exists
