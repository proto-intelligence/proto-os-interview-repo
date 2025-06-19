from pprint import pformat
from loguru import logger
from typing import List, Optional
from app.core.config import settings
from app.integrations.google_calendar.schemas.calendar_metadata_schemas import ApiMethod, \
    SchemaResolver
from app.integrations.google_calendar.fetch_calendar_api_data import create_session, \
    create_retry_strategy, fetch_api_metadata, save_api_json_data
from app.integrations.google_calendar.parse_calendar_api_data import load_file_data, \
    extract_top_level_attributes, get_api_resources_with_methods, get_api_methods
from app.integrations.google_calendar.convert_data_to_csv import convert_api_methods_to_csv


def fetch_api_data() -> str | None:
    """
    Fetches the Google Calendar API Discovery metadata and saves
    it to a local JSON file.

    This function performs the following steps:
    1. Creates a `requests.Session` with retry logic and exponential backoff.
    2. Sends a GET request to the Google Calendar Discovery API.
    3. Saves the response JSON to a timestamped file in the local directory.

    Returns:
        str | None: The absolute file path of the saved JSON file if successful;
        otherwise, None.

    Raises:
        Exception: If any unexpected error occurs during the fetch or save process.

    Logs:
        - Debug information about the request and file creation.
        - Errors related to network issues or file system failures.
    """
    try:
        session = create_session(create_retry_strategy())

        data = fetch_api_metadata(session, settings.GOOGLE_CALENDAR_API_URL)
        if not data:
            return None

        json_path = save_api_json_data(data)
        if not json_path:
            return None

        return json_path
    except Exception as err:
        logger.error(f"An Error has ocurred while fetching and saving json data process: {err}")
        raise

def parse_data(json_path: str) -> Optional[List[ApiMethod]]:
    """
    Parses the Google Calendar API JSON into structured API method objects.

    This function performs the following steps:
    1. Loads the JSON file from the given path.
    2. Extracts the top-level attributes (`parameters`, `schemas`, `resources`).
    3. Resolves all `$ref` references in the schema definitions.
    4. Iterates over API resources and their methods to construct `ApiMethod` objects.

    Args:
        json_path (str): The absolute path to the saved Google Calendar JSON file.

    Returns:
        Optional[List[ApiMethod]]: A list of parsed `ApiMethod` instances, or None if parsing fails.

    Raises:
        Exception: If any error occurs during file loading, schema resolution, or method parsing.

    Logs:
        - Error messages with contextual information if parsing fails at any stage.
    """
    try:
        data = load_file_data(json_path)
        parent_metadata = extract_top_level_attributes(data)
        schemas_resolver = SchemaResolver(schemas=parent_metadata.schemas)
        schemas_resolver.resolve_all()

        resources_with_methods = get_api_resources_with_methods(parent_metadata)
        api_methods = get_api_methods(resources_with_methods, schemas_resolver)

        return api_methods
    except Exception as e:
        logger.error(f"Error in parse_data: {e}.")
        raise

def main_entry_point_function() -> Optional[dict]:
    """
    Executes the full process for fetching, parsing, and saving Google Calendar API metadata.

    This function coordinates the following steps:
    1. Fetches the Google Calendar API document and saves it as a local JSON file.
    2. Parses the saved JSON to extract structured API method metadata using Pydantic models.
    3. Converts the parsed API metadata into a CSV file for easy analysis.

    Returns:
        dict | None: A dictionary with output file paths and method count if successful,
            otherwise None.

    Logs:
        - Warnings if no API methods are found after parsing.
        - Errors if any step in the process fails.
        - Final summary with output file paths and method count.

    Notes:
        - Uses robust error handling to ensure that each phase fails gracefully.
        - Logs structured results for easy traceability and debugging.
        - Can be exposed as a CLI entry point via `if __name__ == "__main__"` or `typer` integration.
    """
    try:
        json_save_path: str = fetch_api_data()
        if not json_save_path:
            logger.error("JSON save path is None. Halting execution.")
            return None

        parsed_api_methods: List[ApiMethod] = parse_data(json_path=json_save_path)

        if not parsed_api_methods:
            logger.warning("No API methods parsed. CSV file will not be created.")
            return None

        csv_save_path: str = convert_api_methods_to_csv(data=parsed_api_methods)

        response = {
            "json_save_path": json_save_path,
            "total_count_api_methods": len(parsed_api_methods),
            "csv_save_path": csv_save_path
        }

        logger.debug(f"Process ends succesfully, see response metadata for the save files")
        logger.info(f"Response:\n{pformat(response)}")

        return response
    except Exception:
        return None


if __name__ == "__main__":
    main_entry_point_function()