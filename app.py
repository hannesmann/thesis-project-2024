# This is the main file for the data collection and risk assessment server.
# It should be run with Poetry following the instructions in the README.
# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

from flask import Flask, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# https://flask-sqlalchemy.palletsprojects.com/en/3.1.x/quickstart/
class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

api = Flask(__name__)
api.config.from_pyfile("config.py")

db.init_app(api)
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

# Run development server if executed directly from Python
if __name__ == "__main__":
	api.run(debug=True)
