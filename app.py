# This is the main file for the data collection and risk assessment server.
# It should be run with Poetry following the instructions in the README.
# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from repository.apps import ApplicationRepository
from repository.devices import DevicesRepository
from importers.devices.importer import DeviceImporterThread

from api.routes import register_routes

# Initialize REST server
api = Flask(__name__)
api.config.from_pyfile("config.py")

logger = logging.getLogger("app")
logger.setLevel(api.config["LOG_LEVEL"])
api.logger.setLevel(api.config["LOG_LEVEL"])

# Initialize database and repositories
db = SQLAlchemy()
db.init_app(api)

application_repo_instance = ApplicationRepository(db)
devices_repo_instance = DevicesRepository(db)

device_importer_thread = DeviceImporterThread(application_repo_instance)

with api.app_context():
    db.create_all()

register_routes(api, {
    "repos": {
		"application": application_repo_instance,
		"devices": devices_repo_instance
	},
    "device_importer": device_importer_thread
})

# Run development server if executed directly from Python
if __name__ == "__main__":
	api.run(debug=True)
