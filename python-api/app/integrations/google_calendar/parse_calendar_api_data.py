import json
from loguru import logger
from typing import Optional, Tuple, Dict, Any, List
from app.integrations.google_calendar.schemas.calendar_metadata_schemas import CalendarMetadataParents, ApiMethod, SchemaResolver


def load_file_data(json_path: str) -> dict:
    """
    Loads JSON data from a specified file path.
    The file to load contains the  API metadata for Google Calendar.
    This function reads the JSON file and returns its content as a dictionary.

    Args:
        json_path (str): The path to the JSON file to be loaded.
    Returns:
        dict: The data loaded from the JSON file.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the file contains invalid JSON.
    """
    try:
        logger.debug(f"Loading JSON data from {json_path}")

        with open(json_path, "r") as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {json_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in file {json_path}: {e}") from e

def extract_top_level_attributes(data: dict) -> CalendarMetadataParents:
    """
    Extracts the top-level attributes ('parameters', 'schemas', 'resources')
    from the Google Calendar API metadata dictionary
    and returns them as a CalendarMetadataParents object.
    This function is used to parse the API metadata and prepare it for further processing.

    Args:
        data (dict): The API metadata dictionary containing top-level attributes
            including 'parameters', 'schemas', and 'resources'.

    Returns:
        CalendarMetadataParents: An object containing the extracted 'parameters', 'schemas', and 'resources' attributes.
    """
    parent_metadata = CalendarMetadataParents(
        parameters = data.get("parameters", {}),
        schemas = data.get("schemas", {}),
        resources = data.get("resources", {})
    )

    if not parent_metadata.resources:
        logger.error("No resources found in API metadata. Ensure the metadata is correct.")
        raise ValueError("No resources found in API metadata.")

    logger.debug("Extracted top-level attributes from API metadata.")
    return parent_metadata

def get_api_resources_with_methods(parent_metadata: CalendarMetadataParents) -> list[dict]:
    """
    Extracts and returns a list of resources with their associated methods from
    the given CalendarMetadataParents object.
    This function processes the 'resources' attribute of the CalendarMetadataParents object,
    filtering out resources that do not have a 'methods' attribute or where 'methods' is not a dictionary.

    Each list of resources contains dictionaries with the following keys:
        - "resource_name" (str): The name of the resource.
        - "methods" (dict): The methods associated with the resource.

    Args:
        parent_metadata (CalendarMetadataParents): The metadata object containing API resource definitions.

    Returns:
        list[dict]: A list of dictionaries, each containing:
            - "resource_name" (str): The name of the resource.
            - "methods" (dict): The methods associated with the resource.

    Raises:
        ValueError: If no resources are found in the metadata, or if no valid resources with methods are found.

    Logs:
        - Warnings if a resource's "methods" attribute is not a dictionary or if an error occurs while processing a resource.
        - Debug message indicating the number of resources with methods found.
    """
    if not parent_metadata.resources:
        raise ValueError("No resources with endpoint's documentation found in API metadata.")

    resources_with_methods = []

    for resource_name, resource in parent_metadata.resources.items():
        try:
            methods = resource.get("methods", {})
            if not isinstance(methods, dict):
                logger.warning(f"'methods' for resource '{resource_name}' is not a dict. Skipping.")
                continue

            resources_with_methods.append({
                "resource_name": resource_name,
                "methods": methods
            })
        except Exception as e:
            logger.warning(f"Error processing resource '{resource_name}': {e}. Skipping.")

    if not resources_with_methods:
        raise ValueError("No valid resources with methods found in API metadata.")

    logger.debug(f"Found {len(resources_with_methods)} resources with methods.")
    return resources_with_methods

def get_api_method_parameters(method_parameters: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Extracts and categorizes API method parameters into required and optional 
    parameters lists.
    This function processes the 'parameters' attribute of an API method,
    identifying which parameters are required and which are optional.
    A parameter is considered required if its value dictionary contains the key "required".

    It returns two lists:
        - required_params: A list of dictionaries representing required parameters, with the "required" key removed.
        - optional_params: A list of dictionaries representing optional parameters.

    A parameter contains the next data-contract:
        {
            "name": "parameter_name",
            "type": "string",  # or other types like "integer", "boolean", etc.
            "description": "A brief description of the parameter",
            "location": "query"  # or "path", "header", etc.
        }

    Args:
        method_parameters (dict): A dictionary where each key is a parameter name and each
            value is a dictionary describing the parameter's attributes. The presence of the "required"
            key in the value dictionary determines if the parameter is required.
    Returns:
        tuple: A tuple containing two lists:
            - required_params (list): List of dictionaries representing required parameters (with "required" key removed).
            - optional_params (list): List of dictionaries representing optional parameters.
    Notes:
        - Parameters whose value is not a dictionary are skipped.
        - If an error occurs while processing a parameter, it is skipped and a warning is logged.
    """
    if not method_parameters:
        return [], []

    required_params: List[Dict[str, Any]] = []
    optional_params: List[Dict[str, Any]] = []

    for name, value in method_parameters.items():
        if not isinstance(value, dict):
            continue  # Skip if value is not a dict

        try:
            parameter_dict = {"name": name, **value}
            if "required" in parameter_dict:
                parameter_dict.pop("required")
                required_params.append(parameter_dict)
            else:
                optional_params.append(parameter_dict)
        except Exception as e:
            logger.warning(f"Error processing parameter '{name}': {e}. Skip it.")

    return required_params, optional_params

def get_request_response_schemas(
    method: dict, schemas_resolver: SchemaResolver
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Extracts and resolves request and response schema attributes from an API method definition.
    Given a method dictionary and a SchemaResolver instance, this function attempts to resolve
    any schema references ("$ref") found in the "request" and "response" attributes of the method.
    If a reference is found, it is resolved using the provided SchemaResolver. If resolution fails,
    the unresolved reference is retained. If no schema is present, empty dictionaries are returned.

    Args:
        method (dict): The API method definition containing "request" and/or "response" attributes.
        schemas_resolver (SchemaResolver): An instance capable of resolving schema references.

    Returns:
        Tuple[Dict[str, Any], Dict[str, Any]]: A tuple containing the processed request and response
        attribute dictionaries, with resolved schemas if applicable.

    Example:
    >>> method = {
        "request": {"$ref": "RequestSchema"},
        "response": {"$ref": "ResponseSchema"}
    }
    """
    request_attrs = method.get("request", {})
    response_attrs = method.get("response", {})

    try:
        if request_attrs:
            if "$ref" in request_attrs:
                ref_schema = request_attrs.pop("$ref")
                try:
                    request_attrs["schema"] = schemas_resolver.get_resolved(ref_schema)
                except Exception as e:
                    logger.warning(f"Failed to resolve request schema ref '{ref_schema}': {e}")
                    request_attrs["schema"] = ref_schema

        if response_attrs:
            if "$ref" in response_attrs:
                ref_schema = response_attrs.pop("$ref")
                try:
                    response_attrs["schema"] = schemas_resolver.get_resolved(ref_schema)
                except Exception as e:
                    logger.warning(f"Failed to resolve response schema ref '{ref_schema}': {e}")
                    response_attrs["schema"] = ref_schema

        return request_attrs, response_attrs
    except Exception as e:
        logger.warning(f"Error processing request/response schemas: {e}")
        return {}, {}

def get_api_methods(resources_with_methods: list[dict], schemas_resolver: SchemaResolver) -> Optional[list[ApiMethod]]:
    """
    Extracts and formats API method information from a list of resource dictionaries.
    Each resource dictionary is expected to contain a "resource_name" and a "methods" dictionary.

    Iterates through each resource, processes its methods, and constructs a list of `ApiMethod` objects
    containing relevant metadata such as HTTP method, path, parameters, and request/response schemas.

    Args:
        resources_with_methods (list[dict]): 
            A list of dictionaries, each representing an API resource with its associated methods.
        schemas_resolver (SchemaResolver): 
            An instance used to resolve request and response schemas for each API method.

    Returns:
        Optional[list[ApiMethod]]: 
            A list of formatted `ApiMethod` objects if any are found, otherwise an empty list.
            Returns None if no valid API methods are processed.
    """

    logger.debug("Formatting API endpoints from resources with methods.")
    formatted_api_endpoints = []

    for resource in resources_with_methods:
        if not isinstance(resource, dict):
            logger.warning(f"Resource is not a dict: {resource}. Skipping resource.")
            continue
    
        try:
            resource_name = resource["resource_name"]
            methods = resource["methods"]
        except KeyError as e:
            logger.warning(f"Missing key in resource: {e}. Skipping resource.")
            continue

        for method_name, method in methods.items():
            try:
                required_params, optional_params = get_api_method_parameters(method.get("parameters", {}))
                request_schema, response_schema = get_request_response_schemas(method, schemas_resolver)

                current_method = ApiMethod(
                    resource_name = resource_name,
                    method_name = method_name,
                    http_method = method.get("httpMethod", ""),
                    path = method.get("path", ""),
                    description = method.get("description", ""),
                    required_params = required_params,
                    optional_params = optional_params,
                    parameter_order = method.get("parameterOrder", []),
                    request_schema = request_schema,
                    response_schema = response_schema
                )

                formatted_api_endpoints.append(current_method)
            except Exception as e:
                logger.warning(f"Error processing method '{method_name}' in resource '{resource_name}': {e}. Skipping method.")
                continue

    logger.debug(f"Formatted {len(formatted_api_endpoints)} API methods.")
    return formatted_api_endpoints
