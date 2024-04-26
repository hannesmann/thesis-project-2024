# This is the main file for the data collection and risk assessment server.
# It should be run with Poetry following the instructions in the README.
# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

from flask import Flask, Response, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import HTTPException

global application_repo_instance, devices_repo_instance

from repository.apps import ApplicationRepository, application_repo_instance
from repository.devices import DevicesRepository, devices_repo_instance

from api.error import APIError, APIErrorType

# Initialize REST server
api = Flask(__name__)
api.config.from_pyfile("config.py")

# Initialize database and repositories
db = SQLAlchemy()
db.init_app(api)

application_repo_instance = ApplicationRepository(db)
devices_repo_instance = DevicesRepository(db)

with api.app_context():
    db.create_all()

# TODO: Add API endpoints
valid_routes = []
endpoints = "API endpoints:\r\n" + "\r\n".join(valid_routes) + "\r\n"

@api.route("/")
def print_routes():
	return Response(endpoints, mimetype="text/plain")

@api.route("/<path:path>")
def print_invalid_route(path):
	return Response(f"Invalid route: /{path}\r\n\r\n{endpoints}", mimetype="text/plain")

# Default error handler for all types of exceptions
@api.errorhandler(Exception)
def handle_exception(error):
	if error is HTTPException:
		return Response(jsonify(APIError(APIErrorType.UNKNOWN)), error.code)
	else:
		return Response(jsonify(APIError(APIErrorType.UNKNOWN)), 500)

# Run development server if executed directly from Python
if __name__ == "__main__":
	api.run(debug=True)
