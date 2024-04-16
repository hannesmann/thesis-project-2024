# KTH Thesis Project 2024

This is the repository for the Bachelor thesis project "Risk Assessment of Managed Smartphones using MDM" by Hannes Mann and Alexander Wigren.

## Data collection and risk assessment server

The project implements a proof-of-concept application for performing data collection and risk assessment in an automated manner. The tasks performed by the server include:

* Exposing a REST API for manual data upload and download
* Collecting app and device lists from multiple sources such as MDM (Microsoft Intune) and CSV files
* Long-term storage in an SQL database
* Risk assessment of application security and privacy risk based on several data points

### Requirements

* Python 3.11
* Pipenv
* A WSGI server such as Gunicorn (included in Pipfile)

### Running the server

```bash
# Install dependencies
pipenv install
# Activate the project's virtualenv
pipenv shell

# Start the server in debug mode (localhost:5000)
python app.py
# Start the server in production mode (localhost:8000)
gunicorn --workers=4 --log-file=- app:api

# Get a list of API endpoints
curl http://localhost:8000
```
