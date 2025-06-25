import pytest
from unittest.mock import patch, MagicMock
from app.integrations.google_calendar.main_entry_point import fetch_api_data, \
    parse_data, main_entry_point_function


@patch("app.integrations.google_calendar.main_entry_point.create_session")
@patch("app.integrations.google_calendar.main_entry_point.create_retry_strategy")
@patch("app.integrations.google_calendar.main_entry_point.fetch_api_metadata")
@patch("app.integrations.google_calendar.main_entry_point.save_api_json_data")
def test_fetch_api_data_success(mock_save, mock_fetch, mock_retry, mock_session):
    mock_session.return_value = MagicMock()
    mock_retry.return_value = MagicMock()
    mock_fetch.return_value = {"test_key": "test_value"}
    mock_save.return_value = "/tmp/test.json"

    result = fetch_api_data()

    assert result == "/tmp/test.json"
    mock_session.assert_called_once()
    mock_fetch.assert_called_once()
    mock_save.assert_called_once()

@patch("app.integrations.google_calendar.main_entry_point.create_session")
@patch("app.integrations.google_calendar.main_entry_point.create_retry_strategy")
@patch("app.integrations.google_calendar.main_entry_point.fetch_api_metadata")
def test_fetch_api_data_fetch_returns_none(mock_fetch, mock_retry, mock_session):
    mock_session.return_value = MagicMock()
    mock_retry.return_value = MagicMock()
    mock_fetch.return_value = None

    result = fetch_api_data()

    assert result is None

@patch("app.integrations.google_calendar.main_entry_point.create_session")
@patch("app.integrations.google_calendar.main_entry_point.create_retry_strategy")
@patch("app.integrations.google_calendar.main_entry_point.fetch_api_metadata")
@patch("app.integrations.google_calendar.main_entry_point.save_api_json_data")
def test_fetch_api_data_save_returns_none(mock_save, mock_fetch, mock_retry, mock_session):
    mock_session.return_value = MagicMock()
    mock_retry.return_value = MagicMock()
    mock_fetch.return_value = {"test_key": "test_value"}
    mock_save.return_value = None

    result = fetch_api_data()

    assert result is None

@patch("app.integrations.google_calendar.main_entry_point.create_session")
@patch("app.integrations.google_calendar.main_entry_point.create_retry_strategy")
@patch("app.integrations.google_calendar.main_entry_point.fetch_api_metadata")
@patch("app.integrations.google_calendar.main_entry_point.save_api_json_data")
def test_fetch_api_data_raises_exception(mock_save, mock_fetch, mock_retry, mock_session):
    mock_session.side_effect = Exception("session error")

    with pytest.raises(Exception) as excinfo:
        fetch_api_data()

    assert "session error" in str(excinfo.value)
    
@patch("app.integrations.google_calendar.main_entry_point.load_file_data")
@patch("app.integrations.google_calendar.main_entry_point.extract_top_level_attributes")
@patch("app.integrations.google_calendar.main_entry_point.SchemaResolver")
@patch("app.integrations.google_calendar.main_entry_point.get_api_resources_with_methods")
@patch("app.integrations.google_calendar.main_entry_point.get_api_methods")
def test_parse_data_success(
    mock_get_api_methods,
    mock_get_api_resources_with_methods,
    mock_schema_resolver,
    mock_extract_top_level_attributes,
    mock_load_file_data
):
    mock_load_file_data.return_value = {"test_key": "test_value"}
    mock_parent_metadata = MagicMock()
    mock_extract_top_level_attributes.return_value = mock_parent_metadata

    mock_resolver_instance = MagicMock()
    mock_schema_resolver.return_value = mock_resolver_instance

    mock_resources_with_methods = MagicMock()
    mock_get_api_resources_with_methods.return_value = mock_resources_with_methods

    expected_methods = [MagicMock(), MagicMock()]
    mock_get_api_methods.return_value = expected_methods

    result = parse_data("dummy_path.json")

    mock_load_file_data.assert_called_once_with("dummy_path.json")
    mock_extract_top_level_attributes.assert_called_once_with(mock_load_file_data.return_value)
    mock_schema_resolver.assert_called_once_with(schemas=mock_parent_metadata.schemas)
    mock_resolver_instance.resolve_all.assert_called_once()
    mock_get_api_resources_with_methods.assert_called_once_with(mock_parent_metadata)
    mock_get_api_methods.assert_called_once_with(mock_resources_with_methods, mock_resolver_instance)
    assert result == expected_methods

@patch("app.integrations.google_calendar.main_entry_point.load_file_data")
@patch("app.integrations.google_calendar.main_entry_point.extract_top_level_attributes")
@patch("app.integrations.google_calendar.main_entry_point.SchemaResolver")
@patch("app.integrations.google_calendar.main_entry_point.get_api_resources_with_methods")
@patch("app.integrations.google_calendar.main_entry_point.get_api_methods")
def test_parse_data_returns_none_when_no_methods(
    mock_get_api_methods,
    mock_get_api_resources_with_methods,
    mock_schema_resolver,
    mock_extract_top_level_attributes,
    mock_load_file_data
):
    mock_load_file_data.return_value = {"test_key": "test_value"}
    mock_parent_metadata = MagicMock()
    mock_extract_top_level_attributes.return_value = mock_parent_metadata

    mock_resolver_instance = MagicMock()
    mock_schema_resolver.return_value = mock_resolver_instance

    mock_resources_with_methods = MagicMock()
    mock_get_api_resources_with_methods.return_value = mock_resources_with_methods

    mock_get_api_methods.return_value = []

    result = parse_data("dummy_path.json")

    assert result == []

@patch("app.integrations.google_calendar.main_entry_point.load_file_data")
def test_parse_data_raises_exception_on_load_file_data_error(mock_load_file_data):
    mock_load_file_data.side_effect = Exception("file error")
    with pytest.raises(Exception) as excinfo:
        parse_data("dummy_path.json")
    assert "file error" in str(excinfo.value)

@patch("app.integrations.google_calendar.main_entry_point.load_file_data")
@patch("app.integrations.google_calendar.main_entry_point.extract_top_level_attributes")
@patch("app.integrations.google_calendar.main_entry_point.SchemaResolver")
@patch("app.integrations.google_calendar.main_entry_point.get_api_resources_with_methods")
@patch("app.integrations.google_calendar.main_entry_point.get_api_methods")
def test_parse_data_raises_exception_on_get_api_methods_error(
    mock_get_api_methods,
    mock_get_api_resources_with_methods,
    mock_schema_resolver,
    mock_extract_top_level_attributes,
    mock_load_file_data
):
    mock_load_file_data.return_value = {"test_key": "test_value"}
    mock_parent_metadata = MagicMock()
    mock_extract_top_level_attributes.return_value = mock_parent_metadata
    mock_schema_resolver.return_value = MagicMock()
    mock_get_api_resources_with_methods.return_value = MagicMock()
    mock_get_api_methods.side_effect = Exception("methods error")

    with pytest.raises(Exception) as excinfo:
        parse_data("dummy_path.json")
    assert "methods error" in str(excinfo.value)

@patch("app.integrations.google_calendar.main_entry_point.convert_api_methods_to_csv")
@patch("app.integrations.google_calendar.main_entry_point.parse_data")
@patch("app.integrations.google_calendar.main_entry_point.fetch_api_data")
def test_main_entry_point_success(mock_fetch_api_data, mock_parse_data, mock_convert_to_csv):
    mock_fetch_api_data.return_value = "/tmp/test.json"
    mock_methods = [MagicMock(), MagicMock()]
    mock_parse_data.return_value = mock_methods
    mock_convert_to_csv.return_value = "/tmp/test.csv"


    result = main_entry_point_function()

    assert result["json_save_path"] == "/tmp/test.json"
    assert result["total_count_api_methods"] == 2
    assert result["csv_save_path"] == "/tmp/test.csv"
    mock_fetch_api_data.assert_called_once()
    mock_parse_data.assert_called_once_with(json_path="/tmp/test.json")
    mock_convert_to_csv.assert_called_once_with(data=mock_methods)

@patch("app.integrations.google_calendar.main_entry_point.fetch_api_data")
def test_main_entry_point_returns_none_when_fetch_api_data_none(mock_fetch_api_data):
    mock_fetch_api_data.return_value = None


    result = main_entry_point_function()
    assert result is None
    mock_fetch_api_data.assert_called_once()

@patch("app.integrations.google_calendar.main_entry_point.parse_data")
@patch("app.integrations.google_calendar.main_entry_point.fetch_api_data")
def test_main_entry_point_returns_none_when_parse_data_returns_none(mock_fetch_api_data, mock_parse_data):
    mock_fetch_api_data.return_value = "/tmp/test.json"
    mock_parse_data.return_value = None


    result = main_entry_point_function()
    assert result is None
    mock_fetch_api_data.assert_called_once()
    mock_parse_data.assert_called_once_with(json_path="/tmp/test.json")

@patch("app.integrations.google_calendar.main_entry_point.parse_data")
@patch("app.integrations.google_calendar.main_entry_point.fetch_api_data")
def test_main_entry_point_returns_none_when_parse_data_returns_empty_list(mock_fetch_api_data, mock_parse_data):
    mock_fetch_api_data.return_value = "/tmp/test.json"
    mock_parse_data.return_value = []


    result = main_entry_point_function()
    assert result is None
    mock_fetch_api_data.assert_called_once()
    mock_parse_data.assert_called_once_with(json_path="/tmp/test.json")

@patch("app.integrations.google_calendar.main_entry_point.convert_api_methods_to_csv")
@patch("app.integrations.google_calendar.main_entry_point.parse_data")
@patch("app.integrations.google_calendar.main_entry_point.fetch_api_data")
def test_main_entry_point_returns_none_on_exception(mock_fetch_api_data, mock_parse_data, mock_convert_to_csv):
    mock_fetch_api_data.side_effect = Exception("fetch error")

    result = main_entry_point_function()
    assert result is None