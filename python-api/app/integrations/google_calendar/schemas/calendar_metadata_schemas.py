from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel


class SchemaResolver:
    """
    SchemaResolver is a utility class for Google Calendar API metadata schemas.
    Those schemas comes from the response of the metadata request, and can contains
    "$ref" configutaions wich we need to resolve.

    Attributes:
        schemas (Dict[str, Any]): A dictionary mapping schema names found on API response to their definitions.
        resolved_schemas (Dict[str, Dict[str, Any]]): A cache of schemas that have been fully resolved.

    Methods:
        __init__(schemas: Dict[str, Any]) -> None:
            Initializes the SchemaResolver with a dictionary of schemas.

        get_resolved(schema_name: str) -> Optional[Dict[str, Any]]:
            Retrieves a resolved schema by its name from the cache, if available.

        resolve_all() -> None:
            Resolves all schemas in the provided dictionary, expanding any nested $ref references, and stores them in the cache.

        _resolve_schema(schema: Dict[str, Any], seen: set[str] = None) -> Dict[str, Any]:
            Recursively resolves a schema, expanding all $ref references. Handles circular references by tracking seen references.
    """
    def __init__(self, schemas: Dict[str, Any]) -> None:
        self.schemas = schemas
        self.resolved_schemas: Dict[str, Dict[str, Any]] = {}

    def get_resolved(self, schema_name: str) -> Optional[Dict[str, Any]]:
        return self.resolved_schemas.get(schema_name)

    def resolve_all(self) -> None:
        for schema_name in self.schemas:
            self.resolved_schemas[schema_name] = self._resolve_schema(self.schemas[schema_name])

    def _resolve_schema(self, schema: Dict[str, Any], seen: set[str] = None) -> Dict[str, Any]:
        """
        Recursively resolve a schema and all its nested $ref entries.
        """
        if seen is None:
            seen = set()

        if isinstance(schema, list):
            return [self._resolve_schema(item, seen) for item in schema]

        if not isinstance(schema, dict):
            return schema  # value is not a dict, return as is

        if "$ref" in schema:
            ref_value = schema["$ref"]

            if ref_value in seen:
                # Avoid circular references
                return {"$ref": ref_value}

            seen.add(ref_value)
            ref_schema = self.schemas.get(ref_value)

            if not ref_schema:
                return {"$ref": ref_value}  # unresolved

            return self._resolve_schema(ref_schema, seen)

        resolved = {}
        for key, value in schema.items():
            resolved[key] = self._resolve_schema(value, seen.copy())
        return resolved


class CalendarMetadataParents(BaseModel):
    """
    Represents metadata top-level information for calendar parents in the Google Calendar integration.

    Attributes:
        parameters (Optional[dict]): Additional parameters related to the calendar metadata.
        schemas (Optional[dict]): Schema definitions associated with the calendar metadata.
        resources (Optional[dict]): Resource information relevant to the calendar metadata.
    """
    parameters: Optional[dict]
    schemas: Optional[dict]
    resources: Optional[dict]


class ApiMethod(BaseModel):
    """
    Represents the metadata for an API endpoint method in the
    Google Calendar integration.

    Attributes:
        resource_name (str): The name of the resource the API method operates on.
        method_name (str): The name of the API method.
        http_method (str): The HTTP method used (e.g., 'GET', 'POST').
        path (str): The endpoint path for the API method.
        description (Optional[str]): A brief description of the API method.
        required_params (List[dict]): A list of dictionaries describing required parameters for the method.
        optional_params (List[dict]): A list of dictionaries describing optional parameters for the method.
        parameter_order (List[str]): The order in which parameters should be provided.
        request_schema (Optional[dict]): The schema for the request payload, if applicable.
        response_schema (Optional[dict]): The schema for the response payload, if applicable.
    """
    resource_name: str
    method_name: str
    http_method: str
    path: str
    description: Optional[str]
    required_params: List[dict]
    optional_params: List[dict]
    parameter_order: List[str]
    request_schema: Optional[dict]
    response_schema: Optional[dict]


