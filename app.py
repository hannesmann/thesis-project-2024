# This is the main file for the data collection and risk assessment server.
# It should be run with Poetry following the instructions in the README.
# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

global application_repo_instance, devices_repo_instance

from repository.apps import ApplicationRepository, application_repo_instance
from repository.devices import DevicesRepository, devices_repo_instance

from api.routes import register_routes

# Initialize REST server
api = Flask(__name__)
api.config.from_pyfile("config.py")
api.logger.setLevel(api.config["LOG_LEVEL"])

# Initialize database and repositories
db = SQLAlchemy()
db.init_app(api)

application_repo_instance = ApplicationRepository(db)
devices_repo_instance = DevicesRepository(db)

with api.app_context():
    db.create_all()

register_routes(api)

# Run development server if executed directly from Python
if __name__ == "__main__":
	api.run(debug=True)
