# This is the main file for the data collection and risk assessment server.
# It should be run with Poetry following the instructions in the README.
# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

import logging
import atexit

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from importers.apps.importer import AppInfoImporterThread
from repository.apps import ApplicationRepository
from repository.devices import DevicesRepository
from importers.devices.importer import DeviceImporterThread

from api.routes import register_routes

# Initialize REST server
api = Flask(__name__)
api.config.from_pyfile("config.py")

logging.basicConfig()
logger = logging.getLogger("app")
logger.setLevel(api.config["LOG_LEVEL"])
api.logger.setLevel(api.config["LOG_LEVEL"])

# Initialize database and repositories
db = SQLAlchemy()
db.init_app(api)

application_repo_instance = ApplicationRepository(db)
devices_repo_instance = DevicesRepository(db)

app_info_importer_thread = AppInfoImporterThread(application_repo_instance)
device_importer_thread = DeviceImporterThread(application_repo_instance, devices_repo_instance)

with api.app_context():
	db.create_all()
	application_repo_instance.load_tables()
	devices_repo_instance.load_tables()

register_routes(api, {
	"repos": {
		"application": application_repo_instance,
		"devices": devices_repo_instance
	},
	"importers": {
		"app_info": app_info_importer_thread,
		"devices": device_importer_thread
	}
})

def save_db():
	with api.app_context():
		application_repo_instance.save_tables()
		devices_repo_instance.save_tables()

atexit.register(save_db)

# Run development server if executed directly from Python
if __name__ == "__main__":
	api.run(debug=True, threaded=False, use_reloader=False)
