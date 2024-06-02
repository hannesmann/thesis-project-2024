# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

import json
import configs

from time import monotonic
from bottle import Bottle, request, response
from loguru import logger
from api.error import *
from api.routes.fetch import define_fetch_routes
from api.routes.importers import define_import_routes

def get_request_logger(origfn):
	def log_request(*args, **kwargs):
		"""Logs all requests using loguru"""

		start = monotonic()
		# Run the original handler
		res = origfn(*args, **kwargs)
		# Measure request time in ms
		diff = (monotonic() - start) * 1000.0

		# Log request and handler time
		logger.info(f"[{request.remote_addr}] {request.method} {request.url.strip('/ ')} in {round(diff, 2)} ms")

		return res
	return log_request

class RESTBottle(Bottle):
	def __init__(self, catchall=True, autojson=True):
		super().__init__(catchall, autojson)
		if configs.main.server.log_requests:
			self.install(get_request_logger)

	def default_error_handler(self, old):
		"""Translates errors to standard format"""

		# Translate status code to error code
		error = ERROR_UNKNOWN
		if old.status_code == 404:
			error = ERROR_INVALID_ROUTE
		elif old.status_code == 405:
			error = ERROR_WRONG_METHOD

		if configs.main.server.log_requests:
			logger.warning(f"[{request.remote_addr}] {request.method} {request.url.strip('/ ')} {old.status_line}")

		response.content_type = "application/json"
		return json.dumps(make_error(error))

def create_rest_api(repositories, importers):
	app = RESTBottle()

	# Routes for fetching internal information from the server
	define_fetch_routes(app, repositories)

	# Route for importing a CSV file
	define_import_routes(app, importers)

	return app
