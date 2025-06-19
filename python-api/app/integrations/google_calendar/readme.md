# Google Calendar API  metadata Parser

This project fetches, parses, and transforms the [Google Calendar API](https://calendar-json.googleapis.com/$discovery/rest?version=v3) metadata into a CSV format using Python.

---

## Objective

The goal of this project is to build a robust, testable microservice that:

1. Fetches the [Google Calendar API document](https://calendar-json.googleapis.com/$discovery/rest?version=v3)
2. Stores the metadata from API into a JSON file
2. Parses JSON file contents into structured data using **Pydantic models**
3. Converts and saves the results into a `.csv`

---

## What Was Done

- Modular based integration into `app/integrations/google_calendar/` divided on four diferent modules:
    - `fetch_calendar_api_data.py`: fetch metadata the data from Google Calendar API including a retry logic for handling requests errors. Then store the results on a timestamped JSON file
    - `parse_calendar_api_data.py`: parses the content of the JSON file structured with `Pydantic` for schemas validation. including request_schema and respons_schema.
    - `convert_data_to_csv`: Store a timestamped CSV file output with formated Google API Calendar methods.
    - `main_entry_point`: Execute all the pre defined modules in a complete process.

- The parsing logic uses `Pydantic` models to validate and structure API method metadata.
   - The `ApiMethod` schema captures fields like `http_method`, `path`, `description`, and `parameter` lists.
   - A custom `SchemaResolver` class recursively resolves all `$ref` fields in the `schemas` ensuring full `request_schema`, and `response_schema` data it's included into the CSV output.
- Error handling, and logging (`loguru`), to output and store logs under the file on `LOGS_FILE` variable. ensuring logs are not lost and can be seen even after run the script.
- Unit test coverage above (90%) using `pytest` and `coverage`

---

## How to Install Dependencies

You should have python >= `3.10.0` to run this service

This project uses `pyproject.toml` to handle dependencies.

```
python -m pip install -e .
```

---

## How to run the service

Excute `main_entry_poin.py` module to run the comple service.

```
python -m app.integrations.google_calendar.main_entry_point
```
This command will:
1. Download the API metadata from Google
2. Save the raw JSON locally (with timestamp)
3. Parse all endpoints using Pydantic validation
4. Save the structured API methods into a CSV file

### Expected Output
On success, you’ll see structured logs indicating each phase completed. Example final output:
```
{
  'json_save_path': '/path/to/calendar_api_discovery_20250618_123456.json',
  'total_count_api_methods': 45,
  'csv_save_path': '/path/to/calendar_api_discovery_20250618_123456.csv'
}
```
- JSON CSV files output into the folder `app/integrations/google_calendar/data`
- Store logs from the process on `app.log` file in the root og the project

## How to run test and Coverage

To run all test execute the next commands:

1. Runs all the tests
```
coverage run -m pytest
```
2. Run Coverage validation percent
```
coverage report --fail-under=90
```
3. generate coverage `HTML` report. result report will be store on the `/htmlcov/index.html` file
```
coverage html
```
