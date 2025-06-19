import os
import tempfile
import csv
import pytest
from unittest import mock
from app.integrations.google_calendar.convert_data_to_csv import convert_api_methods_to_csv

class DummyApiMethod:
    def __init__(self, **kwargs):
        self._data = kwargs

    def model_dump(self):
        return self._data

    def __iter__(self):
        return iter(self._data.items())

    def keys(self):
        return self._data.keys()

    def __getitem__(self, key):
        return self._data[key]

@pytest.fixture
def dummy_methods():
    return [
        DummyApiMethod(
            name="get",
            description="a get endpoint",
            parameters={"key": "100"},
            extra=None
        ),
        DummyApiMethod(
            name="post",
            description="a post endpoint",
            parameters={'key': 101, 'name': 'test name', 'price': 'test_price'},
            extra=""
        ),
    ]

@mock.patch("app.integrations.google_calendar.convert_data_to_csv.fetch_calendar_api_data.generate_file_name")
@mock.patch("app.integrations.google_calendar.convert_data_to_csv.fetch_calendar_api_data.create_directory_if_not_exists")
def test_convert_api_methods_to_csv_creates_csv(mock_create_dir, mock_gen_file, dummy_methods):
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "test.csv")
        mock_gen_file.return_value = "test.csv"
        mock_create_dir.return_value = csv_path

        result_path = convert_api_methods_to_csv(dummy_methods)
        assert result_path == csv_path
        assert os.path.exists(csv_path)

        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]["name"] == "get"
            assert rows[1]["name"] == "post"
            assert rows[0]["parameters"] == '{"key": "100"}'
            assert rows[1]["parameters"] == '{"key": 101, "name": "test name", "price": "test_price"}'

@mock.patch("app.integrations.google_calendar.convert_data_to_csv.fetch_calendar_api_data.generate_file_name")
@mock.patch("app.integrations.google_calendar.convert_data_to_csv.fetch_calendar_api_data.create_directory_if_not_exists")
def test_convert_api_methods_to_csv_empty_data_raises(mock_create_dir, mock_gen_file):
    mock_gen_file.return_value = "test.csv"
    mock_create_dir.return_value = "test.csv"
    with pytest.raises(ValueError, match="No API method data provided for CSV export."):
        convert_api_methods_to_csv([])

@mock.patch("app.integrations.google_calendar.convert_data_to_csv.fetch_calendar_api_data.generate_file_name")
@mock.patch("app.integrations.google_calendar.convert_data_to_csv.fetch_calendar_api_data.create_directory_if_not_exists")
def test_convert_api_methods_to_csv_ioerror(mock_create_dir, mock_gen_file, dummy_methods):
    mock_gen_file.return_value = "test.csv"
    mock_create_dir.return_value = "/invalid/path/test.csv"
    with mock.patch("builtins.open", side_effect=IOError("disk full")):
        with pytest.raises(IOError):
            convert_api_methods_to_csv(dummy_methods)
