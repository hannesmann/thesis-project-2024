# This is the main file for the data collection and risk assessment server
# It should be run with Poetry following the instructions in the README
# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

import sys
import configs

from loguru import logger

from argparse import ArgumentParser
from sqlalchemy import create_engine

from munch import Munch

from api.restful import create_rest_api

from repository.apps import ApplicationRepository
from repository.devices import DevicesRepository

from importers.apps.importer import AppInfoImporterThread
from importers.devices.importer import DeviceImporterThread
from analysis.analyzer import AppAnalyzerThread

from defaults import *

if __name__ == "__main__":
	# Initialize logger
	logger.remove()
	logger.add(sys.stdout, format=default_log_format)

	# Initialize config files
	parser = ArgumentParser(
		prog="main.py", description="Data collection and risk assessment server"
	)

	parser.add_argument("-c", "--config-file", default=default_config_file)
	parser.add_argument("-s", "--secrets-file", default=default_secrets_file)

	args = parser.parse_args()
	if not configs.load(args.config_file, args.secrets_file):
		quit()

	if configs.main.logging.file:
		logger.add(configs.main.logging.file, format=default_log_format)
	if configs.main.server.debug:
		logger.warning("configs.main.server.debug is set. Running Bottle and SQLAlchemy in debug mode.")

	engine = create_engine(configs.main.server.database_url)
	with engine.connect() as conn:
		# Initialize repositories
		app_repository = ApplicationRepository(conn)
		devices_repository = DevicesRepository(conn)

		with app_repository, devices_repository:
			# Initialize importers
			app_info_importer_thread = AppInfoImporterThread(app_repository, default_app_info_importers)
			device_importer_thread = DeviceImporterThread(app_repository, devices_repository, default_device_importers)
			# Initialize analyzers
			app_analyzer_thread = AppAnalyzerThread(app_repository, devices_repository, default_app_analyzers)

			# Initialize Bottle application
			app = create_rest_api(
				repositories=Munch(apps=app_repository, devices=devices_repository),
				importers=Munch(apps=app_info_importer_thread, devices=device_importer_thread)
			)

			logger.info(f"Listening at http://{configs.main.server.host}:{configs.main.server.port}")
			app.run(
				host=configs.main.server.host,
				port=configs.main.server.port,

				debug=configs.main.server.debug,
				quiet=not configs.main.server.debug,

				server=configs.main.server.backend,
			)
