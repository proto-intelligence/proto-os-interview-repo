import os
import tempfile
import json
import pytest
from app.integrations.google_calendar.parse_calendar_api_data import load_file_data, extract_top_level_attributes, get_api_resources_with_methods, get_api_method_parameters, get_request_response_schemas, get_api_methods
from app.integrations.google_calendar.schemas.calendar_metadata_schemas import CalendarMetadataParents, ApiMethod


DUMMY_JSON = {
    "revision": "20250611",
    "resources": {
        "acl": {
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
}

def test_load_file_data_valid_json():
    data = DUMMY_JSON
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
        json.dump(data, tmp)
        tmp_path = tmp.name
    try:
        result = load_file_data(tmp_path)
        assert result == data
    finally:
        os.remove(tmp_path)

def test_load_file_data_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_file_data("non_existent_file.json")

def test_load_file_data_invalid_json():
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
        tmp.write("{invalid_json: true,}")  # malformed JSON
        tmp_path = tmp.name
    try:
        with pytest.raises(ValueError):
            load_file_data(tmp_path)
    finally:
        os.remove(tmp_path)
        
def test_extract_top_level_attributes_all_present():
    data = DUMMY_JSON
    result = extract_top_level_attributes(data)
    assert result.parameters == {}
    assert result.schemas == {}
    assert result.resources == DUMMY_JSON["resources"]

def test_extract_top_level_attributes_with_all_keys():
    data = {
        "parameters": {"foo": "bar"},
        "schemas": {"baz": "qux"},
        "resources": DUMMY_JSON["resources"]
    }
    result = extract_top_level_attributes(data)
    assert result.parameters == {"foo": "bar"}
    assert result.schemas == {"baz": "qux"}
    assert result.resources == DUMMY_JSON["resources"]

def test_extract_top_level_attributes_missing_parameters_and_schemas():
    data = {
        "resources": DUMMY_JSON["resources"]
    }
    result = extract_top_level_attributes(data)
    assert result.parameters == {}
    assert result.schemas == {}
    assert result.resources == DUMMY_JSON["resources"]

def test_extract_top_level_attributes_missing_resources_raises():
    data = {
        "parameters": {"foo": "bar"},
        "schemas": {"baz": "qux"}
    }
    with pytest.raises(ValueError, match="No resources found in API metadata."):
        extract_top_level_attributes(data)

def test_extract_top_level_attributes_empty_resources_raises():
    data = {
        "parameters": {},
        "schemas": {},
        "resources": {}
    }
    with pytest.raises(ValueError, match="No resources found in API metadata."):
        extract_top_level_attributes(data)

def test_get_api_resources_with_methods_basic():

    parent_metadata = CalendarMetadataParents(
        parameters={},
        schemas={},
        resources=DUMMY_JSON["resources"]
    )

    result = get_api_resources_with_methods(parent_metadata)
    assert isinstance(result, list)
    assert len(result) == 1
    assert "delete" in result[0]["methods"]
    assert result[0]["methods"]["delete"]["id"] == "calendar.acl.delete"

def test_get_api_resources_with_methods_skips_non_dict_methods():

    data = DUMMY_JSON.copy()
    data['resources']['methods'] = ["not", "a", "dict"]

    parent_metadata = CalendarMetadataParents(
        parameters={},
        schemas={},
        resources=data['resources']
    )

    result = get_api_resources_with_methods(parent_metadata)
    assert len(result) == 1
    assert result[0]["resource_name"] == "acl"

def test_get_api_resources_with_methods_empty_resources_raises():

    parent_metadata = CalendarMetadataParents(parameters={}, schemas={}, resources={})
    with pytest.raises(ValueError, match="No resources with endpoint's documentation found in API metadata."):
        get_api_resources_with_methods(parent_metadata)

def test_get_api_resources_with_methods_no_valid_methods_raises():

    parent_metadata = CalendarMetadataParents(
        parameters={},
        schemas={},
        resources={
            "acl": {
                "methods": ["not", "a", "dict"]
            }
        }
    )
    with pytest.raises(ValueError, match="No valid resources with methods found in API metadata."):
        get_api_resources_with_methods(parent_metadata)

def test_get_api_resources_with_methods_handles_exceptions_gracefully(monkeypatch):

    class BadDict(dict):
        def get(self, *args, **kwargs):
            raise Exception("bad get")

    parent_metadata = CalendarMetadataParents(
        parameters={},
        schemas={},
        resources={
            "bad_resource": BadDict()
        }
    )
    # Should raise ValueError because no valid resources with methods are found
    with pytest.raises(ValueError, match="No valid resources with methods found in API metadata."):
        get_api_resources_with_methods(parent_metadata)
        
def test_get_api_method_parameters_empty():
    required, optional = get_api_method_parameters({})
    assert required == []
    assert optional == []

def test_get_api_method_parameters_none():
    required, optional = get_api_method_parameters(None)
    assert required == []
    assert optional == []

def test_get_api_method_parameters_required_and_optional():
    params = {
        "calendarId": {
            "type": "string",
            "description": "Calendar identifier.",
            "required": True,
            "location": "path"
        },
        "maxResults": {
            "type": "integer",
            "description": "Maximum number of entries returned on one result page.",
            "location": "query"
        }
    }
    required, optional = get_api_method_parameters(params)
    assert len(required) == 1
    assert required[0]["name"] == "calendarId"
    assert "required" not in required[0]
    assert required[0]["type"] == "string"
    assert len(optional) == 1
    assert optional[0]["name"] == "maxResults"
    assert optional[0]["type"] == "integer"

def test_get_api_method_parameters_skips_non_dict():
    params = {
        "calendarId": "should be dict",
        "maxResults": {
            "type": "integer",
            "description": "Maximum number of entries.",
            "location": "query"
        }
    }
    required, optional = get_api_method_parameters(params)
    assert required == []
    assert len(optional) == 1
    assert optional[0]["name"] == "maxResults"

def test_get_api_method_parameters_required_key_false():
    params = {
        "calendarId": {
            "type": "string",
            "description": "Calendar identifier.",
            "required": False,
            "location": "path"
        }
    }
    required, optional = get_api_method_parameters(params)
    # Even if required is False, it is treated as required and removed from dict
    assert len(required) == 1
    assert required[0]["name"] == "calendarId"
    assert "required" not in required[0]
    assert optional == []

def test_get_api_method_parameters_handles_exception(monkeypatch):
    class BadDict(dict):
        def items(self):
            raise Exception("bad items")
    params = BadDict()
    required, optional = get_api_method_parameters(params)
    assert required == []
    assert optional == []

def test_get_request_response_schemas_no_refs():
    method = {
        "request": {"type": "object", "description": "Request body"},
        "response": {"type": "object", "description": "Response body"}
    }
    class DummyResolver:
        def get_resolved(self, ref):
            return {"resolved": ref}
    req, resp = get_request_response_schemas(method, DummyResolver())
    assert req == {"type": "object", "description": "Request body"}
    assert resp == {"type": "object", "description": "Response body"}

def test_get_request_response_schemas_with_refs():
    method = {
        "request": {"$ref": "RequestSchema"},
        "response": {"$ref": "ResponseSchema"}
    }
    class DummyResolver:
        def get_resolved(self, ref):
            return {"resolved": ref}
    req, resp = get_request_response_schemas(method, DummyResolver())
    assert req["schema"] == {"resolved": "RequestSchema"}
    assert resp["schema"] == {"resolved": "ResponseSchema"}

def test_get_request_response_schemas_with_ref_resolution_failure(monkeypatch):
    method = {
        "request": {"$ref": "RequestSchema"},
        "response": {"$ref": "ResponseSchema"}
    }
    class FailingResolver:
        def get_resolved(self, ref):
            raise Exception("fail")
    req, resp = get_request_response_schemas(method, FailingResolver())
    assert req["schema"] == "RequestSchema"
    assert resp["schema"] == "ResponseSchema"

def test_get_request_response_schemas_empty_method():
    class DummyResolver:
        def get_resolved(self, ref):
            return {"resolved": ref}
    req, resp = get_request_response_schemas({}, DummyResolver())
    assert req == {}
    assert resp == {}

def test_get_api_methods_basic():
    class DummyResolver:
        def get_resolved(self, ref):
            return {"resolved": ref}

    resources_with_methods = [
        {
            "resource_name": "acl",
            "methods": {
                "delete": {
                    "id": "calendar.acl.delete",
                    "path": "calendars/{calendarId}/acl/{ruleId}",
                    "httpMethod": "DELETE",
                    "description": "Deletes an access control rule.",
                    "parameters": {
                        "calendarId": {
                            "type": "string",
                            "description": "Calendar identifier.",
                            "required": True,
                            "location": "path"
                        }
                    }
                }
            }
        }
    ]

    result = get_api_methods(resources_with_methods, DummyResolver())
    assert isinstance(result, list)
    assert len(result) == 1
    method = result[0]
    assert isinstance(method, ApiMethod)
    assert method.resource_name == "acl"
    assert method.method_name == "delete"
    assert method.http_method == "DELETE"
    assert method.path == "calendars/{calendarId}/acl/{ruleId}"
    assert method.description.startswith("Deletes")
    assert method.required_params[0]["name"] == "calendarId"
    assert method.optional_params == []
    assert method.request_schema == {}
    assert method.response_schema == {}

def test_get_api_methods_with_schema_refs():
    class DummyResolver:
        def get_resolved(self, ref):
            return {"resolved": ref}

    resources_with_methods = [
        {
            "resource_name": "events",
            "methods": {
                "insert": {
                    "id": "calendar.events.insert",
                    "path": "calendars/{calendarId}/events",
                    "httpMethod": "POST",
                    "description": "Creates an event.",
                    "parameters": {},
                    "request": {"$ref": "EventRequest"},
                    "response": {"$ref": "EventResponse"}
                }
            }
        }
    ]

    result = get_api_methods(resources_with_methods, DummyResolver())
    assert len(result) == 1
    method = result[0]
    assert method.request_schema["schema"] == {"resolved": "EventRequest"}
    assert method.response_schema["schema"] == {"resolved": "EventResponse"}

def test_get_api_methods_handles_non_dict_resource():
    class DummyResolver:
        def get_resolved(self, ref):
            return {"resolved": ref}

    resources_with_methods = [
        "not_a_dict"
    ]

    result = get_api_methods(resources_with_methods, DummyResolver())
    assert result == []

def test_get_api_methods_missing_keys():
    class DummyResolver:
        def get_resolved(self, ref):
            return {"resolved": ref}

    resources_with_methods = [
        {"methods": {}}  # missing resource_name
    ]

    result = get_api_methods(resources_with_methods, DummyResolver())
    assert result == []

def test_get_api_methods_method_processing_exception(monkeypatch):
    class DummyResolver:
        def get_resolved(self, ref):
            return {"resolved": ref}

    # Patch get_api_method_parameters to raise
    import app.integrations.google_calendar.parse_calendar_api_data as mod

    def bad_get_api_method_parameters(params):
        raise Exception("fail")

    monkeypatch.setattr(mod, "get_api_method_parameters", bad_get_api_method_parameters)

    resources_with_methods = [
        {
            "resource_name": "acl",
            "methods": {
                "delete": {
                    "id": "calendar.acl.delete",
                    "path": "calendars/{calendarId}/acl/{ruleId}",
                    "httpMethod": "DELETE",
                    "description": "Deletes an access control rule.",
                    "parameters": {}
                }
            }
        }
    ]
    result = mod.get_api_methods(resources_with_methods, DummyResolver())
    assert result == []

def test_get_api_methods_empty_input():
    class DummyResolver:
        def get_resolved(self, ref):
            return {"resolved": ref}
    result = get_api_methods([], DummyResolver())
    assert result == []
