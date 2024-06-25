# KTH Thesis Project 2024

This is the repository for the Bachelor thesis project "Risk Assessment of Managed Smartphones using MDM" by Hannes Mann and Alexander Wigren.

## Data collection and risk assessment server

The project implements a proof-of-concept application for performing data collection and risk assessment in an automated manner. The tasks performed by the server include:

* Exposing a REST API for manual data upload and download
* Collecting app and device lists from multiple sources such as MDM (Microsoft Intune) and CSV files
* Long-term storage in an SQL database
* Risk assessment of application security and privacy risk based on several data points

### Requirements

* Python 3.10 or newer
* Poetry
* A WSGI server such as Waitress (included in pyproject.toml)
* wkhtmltopdf (If you have trouble with the PDF being unreadable by GPT, use a binary from [wkhtmltopdf.org](https://wkhtmltopdf.org/downloads.html))

### Running the server

Before starting the server, API keys should be added in `secrets.toml`. For more detailed instructions on setting up keys for Microsoft Intune, see [docs/intune.md](docs/intune.md).

```bash
# Install dependencies
poetry install
# Activate the project's virtualenv
poetry shell

# Start the server with default config file paths
python main.py
# Start the server with custom config file paths
python main.py --config-file /my/dir/config.toml --secrets-file /my/dir/secrets.toml
```

### REST API

The server provides a REST API at `http://localhost:8000` by default. The REST API can be used to fetch internal data from the server (for example, to build a frontend application) and, if needed, upload data such as app and device lists manually. **The server currently implements no form of authentication and should not be exposed to the public internet.**

#### Response format

The server returns responses as JSON blobs. The blob will have a field `status` that indicates if the request was successful or not. If `status` is set to `error`, the `error` field contains the error code (`invalid_route`, `csv_parse_error`, etc). Otherwise, the blob contains additional fields depending on the API endpoint.

#### Fetching data

The server provides several endpoints for fetching internal data:

```bash
# Get an overview of server state
# This includes app count, device count and (TODO) the current status of importers and analyzers
curl "http://localhost:8000/api/overview"

# Get a list of all discovered apps
curl "http://localhost:8000/api/apps"
# Get a list of all discovered devices
curl "http://localhost:8000/api/devices"

# Get app by ID
# This returns a "data" attribute containing static app data and a "risk_score" attribute containing the latest determined risk score
curl "http://localhost:8000/api/app/android/com.facebook.katana"
curl "http://localhost:8000/api/app/ios/com.facebook.facebook"

# Get device by MDM ID
curl "http://localhost:8000/api/device/57ec137c-7e81-43fe-bd78-1b53468d7968"
```

#### Uploading CSV data

Uploading a list of apps manually can be done with cURL:

```bash
# Replace "apps.csv" with the name of your CSV file
curl --data-binary "@apps.csv" "http://localhost:8000/api/upload_android_csv"
curl --data-binary "@apps.csv" "http://localhost:8000/api/upload_ios_csv"
```

Example files used in the thesis project are provided in `thesis/`.
