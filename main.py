# This is the main file for the data collection and risk assessment server.
# It should be run with Poetry following the instructions in the README.
# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

import logging
import atexit

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from analysis.gpt import GPTAnalyzer
from analysis.trackers import TrackerAnalyzer

from importers.apps.exodus import ExodusImporter
from importers.apps.urls import AppStoreImporter, PlayStoreImporter

from repository.apps import ApplicationRepository
from repository.devices import DevicesRepository

from analysis.analyzer import AppAnalyzerThread
from importers.apps.importer import AppInfoImporterThread
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

with api.app_context():
	db.create_all()
	application_repo_instance.load_tables()
	devices_repo_instance.load_tables()

app_info_importer_thread = AppInfoImporterThread(application_repo_instance)
device_importer_thread = DeviceImporterThread(application_repo_instance, devices_repo_instance)

# Add store importers
app_info_importer_thread.add_importer(AppStoreImporter())
app_info_importer_thread.add_importer(PlayStoreImporter())

# Add Exodus importer
if api.config["EXODUS_API_KEY"]:
	app_info_importer_thread.add_importer(ExodusImporter(api.config["EXODUS_API_KEY"]))
else:
	logger.warning("EXODUS_API_KEY is not set. The Exodus Privacy API will not be used for fetching permissions and trackers.")

app_analyzer_thread = AppAnalyzerThread(application_repo_instance)

# Add GPT analyzer
if not api.config["OPENAI_API_KEY"]:
	logger.fatal("OPENAI_API_KEY is not set. The GPT analyzer needs access to the OpenAI API to function.")
	quit()

app_analyzer_thread.add_analyzer(GPTAnalyzer(api.config["OPENAI_API_KEY"], api.config["OPENAI_MODEL"]))
if api.config["EXODUS_API_KEY"]:
	app_analyzer_thread.add_analyzer(TrackerAnalyzer(api.config["EXODUS_API_KEY"]))

register_routes(api, {
	"repos": {
		"application": application_repo_instance,
		"devices": devices_repo_instance
	},
	"analysis_thread": app_analyzer_thread,
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

# Test the gpt thingymading lol remove this after testing



