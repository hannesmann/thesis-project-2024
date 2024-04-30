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
* A WSGI server such as Gunicorn (included in pyproject)

### Running the server

```bash
# Install dependencies
poetry install
# Activate the project's virtualenv
poetry shell

# Start the server in debug mode (localhost:5000)
python main.py
# Start the server in production mode (localhost:8000)
gunicorn --workers=1 --worker-class=thread --log-file=- main:api

# Get a list of API endpoints
curl http://localhost:8000
```

### Uploading CSV data

Uploading a list of apps manually can be done with cURL:

```bash
# Replace "apps.csv" with the name of your CSV file
curl --data-binary "@apps.csv" "http://localhost:8000/api/upload_android_csv"
curl --data-binary "@apps.csv" "http://localhost:8000/api/upload_ios_csv"
```
