
import json
import os
import pytest
from urllib3.util import Retry
from app.integrations.google_calendar.fetch_calendar_api_data import create_retry_strategy, create_session, fetch_api_metadata, save_api_json_data, create_directory_if_not_exists
from app.integrations.google_calendar import fetch_calendar_api_data

DUMMY_JSON = {
    "revision": "20250611",
    "resources": {
        "methods": {
            "delete": {
                "id": "calendar.acl.delete",
                "path": "calendars/{calendarId}/acl/{ruleId}",
                "httpMethod": "DELETE",
                "description": "Deletes an access control rule.",
                "parameters": {
                    "calendarId": {
                        "type": "string",
                        "description": "Calendar identifier. To retrieve calendar IDs call the calendarList.list method. If you want to access the primary calendar of the currently logged in user, use the \"primary\" keyword.",
                        "required": True,
                        "location": "path"
                    }
                }
            }
        }
    }
}


def test_create_retry_strategy_returns_retry_object():
    retry = create_retry_strategy()
    assert isinstance(retry, Retry)

def test_create_retry_strategy_configuration():
    retry = create_retry_strategy()
    assert retry.total == 4
    assert retry.backoff_factor == 0.5
    assert set(retry.status_forcelist) == {429, 500, 502, 503, 504}
    # allowed_methods is a frozenset in urllib3 Retry
    assert set(retry.allowed_methods) == {"GET"}

def test_create_session_success(monkeypatch):
    class DummyAdapter:
        def __init__(self, max_retries):
            self.max_retries = max_retries
        def __call__(self, *args, **kwargs):
            return self

    class DummySession:
        def __init__(self):
            self.mounted = {}
        def mount(self, prefix, adapter):
            self.mounted[prefix] = adapter

    # Patch HTTPAdapter and requests.Session
    monkeypatch.setattr(fetch_calendar_api_data, "HTTPAdapter", DummyAdapter)
    monkeypatch.setattr(fetch_calendar_api_data.requests, "Session", DummySession)

    retry = create_retry_strategy()
    session = create_session(retry)
    assert isinstance(session, DummySession)
    assert "https://" in session.mounted
    assert session.mounted["https://"].max_retries == retry

def test_create_session_exception(monkeypatch):
    def raise_adapter(*args, **kwargs):
        raise RuntimeError("adapter error")
    monkeypatch.setattr(fetch_calendar_api_data, "HTTPAdapter", raise_adapter)

    retry = create_retry_strategy()
    with pytest.raises(RuntimeError):
        create_session(retry)

def test_fetch_api_metadata_success(monkeypatch):
    class DummyResponse:
        def __init__(self):
            self._json = DUMMY_JSON

        def raise_for_status(self):
            pass

        # Simulate a successful JSON response
        def json(self):
            return self._json

    class DummySession:
        def get(self, url, timeout, verify):
            assert url == "http://a-trust-integration-test-url.com"
            return DummyResponse()

    session = DummySession()
    url = "http://a-trust-integration-test-url.com"
    result = fetch_api_metadata(session, url)
    assert result == DUMMY_JSON

def test_fetch_api_metadata_http_error(monkeypatch):
    class DummyResponse:
        def raise_for_status(self):
            raise fetch_calendar_api_data.requests.exceptions.HTTPError("bad status")
        def json(self):
            return {}

    class DummySession:
        def get(self, url, timeout, verify):
            return DummyResponse()

    session = DummySession()
    url = "http://a-trust-integration-test-url.com"
    result = fetch_api_metadata(session, url)
    assert result is None

def test_fetch_api_metadata_request_exception(monkeypatch):
    class DummySession:
        def get(self, url, timeout, verify):
            raise fetch_calendar_api_data.requests.exceptions.RequestException("network error")

    session = DummySession()
    url = "http://a-trust-integration-test-url.com"
    result = fetch_api_metadata(session, url)
    assert result is None

def test_create_directory_if_not_exists_creates_dir_and_returns_path(tmp_path, monkeypatch):
    # Patch __file__ to simulate current file location
    fake_file = tmp_path / "fake_script.py"
    fake_file.write_text("# dummy")
    monkeypatch.setattr(fetch_calendar_api_data, "__file__", str(fake_file))

    file_name = "testfile.json"
    result_path = create_directory_if_not_exists(file_name)
    expected_dir = tmp_path / "data"
    expected_path = expected_dir / file_name

    assert os.path.isdir(expected_dir)
    assert result_path == str(expected_path)

def test_create_directory_if_not_exists_oserror(monkeypatch):
    # Patch os.makedirs to raise OSError
    monkeypatch.setattr(fetch_calendar_api_data, "__file__", "/tmp/fake.py")
    def raise_oserror(*args, **kwargs):
        raise OSError("permission denied")
    monkeypatch.setattr(fetch_calendar_api_data.os, "makedirs", raise_oserror)

    with pytest.raises(Exception) as excinfo:
        fetch_calendar_api_data.create_directory_if_not_exists("fail.json")
    assert "Failed to create directory" in str(excinfo.value)

def test_generate_file_name_format(monkeypatch):
    # Patch time.strftime to return a fixed timestamp
    monkeypatch.setattr("time.strftime", lambda fmt: "20250618_123456")
    result = fetch_calendar_api_data.generate_file_name("test_file", "json")
    assert result == "test_file_20250618_123456.json"

def test_generate_file_name_with_different_inputs(monkeypatch):
    monkeypatch.setattr("time.strftime", lambda fmt: "20250619_000000")
    assert fetch_calendar_api_data.generate_file_name("data", "json") == "data_20250619_000000.json"
    assert fetch_calendar_api_data.generate_file_name("backup", "bak") == "backup_20250619_000000.bak"

def test_save_api_json_data_success(monkeypatch, tmp_path):
    # Patch generate_file_name to return a fixed filename
    monkeypatch.setattr(fetch_calendar_api_data, "generate_file_name", lambda n, e: "testfile.json")
    # Patch create_directory_if_not_exists to return a file path in tmp_path
    monkeypatch.setattr(fetch_calendar_api_data, "create_directory_if_not_exists", lambda fn: str(tmp_path / fn))
    data = DUMMY_JSON
    result = save_api_json_data(data)

    assert result == str(tmp_path / "testfile.json")

    with open(result, "r") as f:
        saved = json.load(f)
    assert saved == data

def test_save_api_json_data_ioerror(monkeypatch):
    monkeypatch.setattr(fetch_calendar_api_data, "generate_file_name", lambda n, e: "testfile.json")
    monkeypatch.setattr(fetch_calendar_api_data, "create_directory_if_not_exists", lambda fn: "/invalid/path/testfile.json")
    # Patch open to raise IOError
    def raise_ioerror(*args, **kwargs):
        raise IOError("disk full")

    monkeypatch.setattr("builtins.open", raise_ioerror)

    data = DUMMY_JSON
    result = save_api_json_data(data)
    assert result is None

def test_save_api_json_data_unexpected_exception(monkeypatch):
    monkeypatch.setattr(fetch_calendar_api_data, "generate_file_name", lambda n, e: "testfile.json")
    monkeypatch.setattr(fetch_calendar_api_data, "create_directory_if_not_exists", lambda fn: "testfile.json")
    # Patch json.dump to raise an unexpected exception
    monkeypatch.setattr(fetch_calendar_api_data.json, "dump", lambda *a, **k: (_ for _ in ()).throw(ValueError("unexpected")))
    data = {"foo": "bar"}
    result = save_api_json_data(data)
    assert result is None
