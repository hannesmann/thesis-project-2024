# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

from bottle import request, response
from loguru import logger
from api.error import *
from importers.devices.csv import CSVImporter
from model.app import OperatingSystem

def define_import_routes(app, importers):
	@app.route("/api/upload_<os>_csv", method="POST")
	def upload_csv(os):
		try:
			importer = CSVImporter(request.body.read().decode("utf-8"), OperatingSystem(os))
			logger.info(f"CSV uploaded with {len(importer.apps)} apps")
			importers.devices.queue_import(importer)
			return make_success({"imported_count": len(importer.apps)})
		except Exception as e:
			logger.error(f"CSV parsing failed: {e}")
			response.status = 400
			return make_error(ERROR_CSV_PARSE_ERROR)
