import pytest
from tests.fixtures import loader, test_data_path, test_data_path_tcx, session_temp


def test_extract(loader, test_data_path) -> None:
    "Test the extract method of the LocalDataLoader class"

    dirctory, expected_results = test_data_path

    results = loader.extract(dirctory)

    assert results == expected_results


def test_extract_tcx(loader, test_data_path_tcx) -> None:
    "Test the extract method of the LocalDataLoader class"

    dirctory, expected_results = test_data_path_tcx

    results = loader.extract(dirctory)

    assert results["xml_data"] == expected_results


def test_extract_bad_format(loader) -> None:
    "Test the extract method of the LocalDataLoader class for bad file format"
    file_extension = ".csv"
    path = f"fakedir/fakefile{file_extension}"
    with pytest.raises(
        ValueError, match=f"file type {file_extension} is not supported"
    ):
        loader.extract(path)


def test_load(loader, capsys) -> None:
    data = [{"name1": "value1"}, {"name2": "value2"}]

    loader.load(data, "test_table")
    captured = capsys.readouterr()
    expected_value = "test_table {'name1': 'value1'}\ntest_table {'name2': 'value2'}\n"
    assert captured.out == expected_value
