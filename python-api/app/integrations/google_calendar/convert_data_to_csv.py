import json
import csv
from loguru import logger
from app.integrations.google_calendar.schemas.calendar_metadata_schemas import ApiMethod
from app.integrations.google_calendar import fetch_calendar_api_data


def convert_api_methods_to_csv(data: list[ApiMethod]) -> str:
    """
    Converts a list of ApiMethod objects (endpoints metadata) to a CSV file.

    This function takes a list of ApiMethod instances, processes each object
    and writes the data to a CSV file.
    The CSV file is created in /data directory and the file path is returned.

    Args:
        data (list[ApiMethod]): A list of ApiMethod objects to be exported to CSV.

    Returns:
        str: The file path to the generated CSV file.

    Raises:
        ValueError: If the input data list is empty.
        IOError: If an I/O error occurs while writing the file.
        Exception: For any other unexpected errors during the CSV conversion process.
    """
    
    filename = fetch_calendar_api_data.generate_file_name("calendar_api_discovery", "csv")
    filepath = fetch_calendar_api_data.create_directory_if_not_exists(filename)

    try:
        if not data:
            raise ValueError("No API method data provided for CSV export.")

        column_names = list(dict(data[0]).keys())

        with open(filepath, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=column_names)
            writer.writeheader()

            for row_dict in data:
                processed_row = {}
                dict_data = row_dict.model_dump()

                for key, value in dict_data.items():
                    if not value:  # empty dicts or list will be ""
                        processed_row[key] = ""
                    elif isinstance(value, (dict, list)):
                        # convert nested dictionaries into their str representation
                        processed_row[key] = json.dumps(value)
                    else:
                        processed_row[key] = value
                writer.writerow(processed_row)
        logger.debug(f"{len(data)} API methods were successfully written to CSV {filename}")
        return filepath
    except IOError as ioe:
        logger.error(f"IO error while writing to {filename}: {ioe}")
        raise
    except Exception as err:
        logger.error(f"Unexpected error during CSV conversion: {err}")
        raise
