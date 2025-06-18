import logging
import os
import json
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from loguru import logger
# local imports
from app.core.config import settings
from app.core.logging import configure_logging


# Enable detailed urllib3 logging
logging.getLogger("urllib3").setLevel(settings.LOGS_LEVEL)


def create_retry_strategy() -> Retry:
    """
    Creates and returns a Retry strategy for HTTP requests.

    This strategy retries failed GET requests up to 4 times
    with exponential backoff (0.5, 1.0, 2.0, 4.0 seconds)

    for specific HTTP status codes:
        - 429 (Too Many Requests)
        - 500 (Internal Server Error)
        - 502 (Bad Gateway)
        - 503 (Service Unavailable)
        - 504 (Gateway Timeout)

    Returns:
        Retry: A configured Retry instance object for use 
        with HTTP requests.
    """
    return Retry(
        total=4, # retry up to 4 times
        backoff_factor=0.5, # exponential backoff 0.5, 1.0, 2.0, 4.0 seconds
        status_forcelist=[429, 500, 502, 503, 504], # Retry on these HTTP status codes
        allowed_methods=["GET"]
    )

def create_session(retry_strategy: Retry) -> requests.Session:
    """
    Creates and configures a requests.Session
    object with a specified retry strategy.

    This function attaches the retry strategy to the session
    using an HTTPAdapter, which ensures that all HTTPS requests
    made with this session will automatically use the retry logic.

    Args:
        retry_strategy (Retry): An instance of urllib3.util.retry.Retry
            that defines the retry logic for HTTP requests.

    Returns:
        requests.Session: A session object with the retry
        strategy applied to all HTTPS requests.

    Raises:
        Exception: If the session creation fails, an exception is raised
        with a message indicating the failure.
    """
    try:
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session = requests.Session()
        session.mount("https://", adapter)
        return session
    except Exception as e:
        logger.error(f"Failed to create requests session: {e}")
        raise

def fetch_api_metadata(session: requests.Session, url: str) -> dict | None:
    """
    Fetches metadata from a specified URL using a provided requests session.
    This function makes a GET request to the given URL and returns the
    JSON response as a dictionary if the request is successful.

    The session is expected to have a retry strategy applied, which will
    handle retries for certain HTTP errors and connection issues.

    If the request fails due to an HTTP error or any other request exception,
    it logs the error and returns None.

    Args:
        session (requests.Session): The session object to use for making the HTTP request.
        url (str): The URL of the Google Calendar API endpoint to fetch metadata from.

    Returns:
        dict | None: The JSON response as a dictionary if the request is successful, otherwise None.

    Raises:
        requests.exceptions.HTTPError: If the HTTP request returns an unsuccessful status code.
        requests.exceptions.RequestException: If there is a network-related error.

    Logs:
        - Debug message when fetching metadata.
        - Error messages for HTTP errors or other request exceptions.
    """
    try:
        logger.debug(f"Fetching API metadata from: {url}")
        # If a request fails with a status code in status_forcelist,
        # or due to a connection error, the session will automatically retry
        response = session.get(url=url, timeout=5, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error: {str(http_err)}")
    except requests.exceptions.RequestException as err:
        logger.error(f"Request failed: {str(err)}")

    return None

def create_directory_if_not_exists(file_name: str) -> None:
    """
    Create a data directory if it does not already exist.
    This function constructs a path to a 'data' directory
    within the current working directory, and creates it if it
    does not exist.

    It then returns the full path to the specified file
    within that directory.

    Parameters:
        cwd (str): The current directory path.

    Returns:
        str: The full path to the specified file within the 'data' directory.

    Raises:
        Exception: If the directory creation fails, an exception is raised
        with a message indicating the failure.
    """
    try:
        cwd = os.path.dirname(os.path.abspath(__file__)) #  get current working directory
        data_dir = os.path.join(cwd, "data")
        os.makedirs(data_dir, exist_ok=True)
    except OSError as e:
        raise Exception(f"Failed to create directory {data_dir}: {e}")

    return os.path.join(data_dir, file_name)

def generate_file_name(file_name: str, extension: str) -> str:
    """
    Generates a timestamped filename for saving data.

    The filename is formatted as:
        {file_name}_YYYYMMDD_HHMMSS.{extension}

    Returns:
        str: The generated filename with the current timestamp.
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    return f"{file_name}_{timestamp}.{extension}"


def save_api_json_data(data: dict) -> str | None:
    """
    Saves the provided metadata from API requests as a
    JSON file with a timestamped filename.

    This function creates a 'data' directory if it does not exist,
    and saves the JSON data to a file named with the current timestamp.

    Args:
        data (dict): The API metadata to be saved in JSON format.
    
    Returns:
        str | None: The file path of the saved JSON file if successful, otherwise None.
    
    Logs:
        - Info: When the file is successfully saved.
        - Error: If an IOError or any unexpected exception occurs during the save process.
    
    Raises:
        IOError: If there is an issue writing to the file.
        Exception: If an unexpected error occurs during the save process.
    """
    try:
        filename = generate_file_name("calendar_api_discovery", "json")
        filepath = create_directory_if_not_exists(filename)

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Google Calendar API metadata saved to {filepath}.")
        return filepath
    except IOError as file_err:
        logger.error(f"Unexpected error occurred while saving API metadata to file: {file_err}")
        return None
    except Exception as err:
        logger.error(f"Unexpected error while saving API metadata: {err}")
        return None
