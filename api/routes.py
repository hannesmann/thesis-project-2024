# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

from flask import Response, request
from api.error import APIErrorType, make_success, make_error
from functools import partial

from importers.devices.csv import CSVImporter
from model.app import OperatingSystem

def upload_csv(api, devices_importer_thread, os):
	if request.method == "POST":
		try:
			importer = CSVImporter(request.get_data(as_text=True), os)
			api.logger.info(f"CSV uploaded with {len(importer.apps)} app(s)")
			devices_importer_thread.add_importer(importer)
			return make_success({"apps": len(importer.apps)}), 200
		except Exception as e:
			api.logger.error(f"CSV parsing fail: {e}")
			return make_error(APIErrorType.PARSE_ERROR), 400
	else:
		return make_error(APIErrorType.WRONG_METHOD), 400

valid_routes = [
	"POST /api/upload_android_csv",
	"POST /api/upload_ios_csv"
]
endpoints = "API endpoints:\r\n" + "\r\n".join(valid_routes) + "\r\n"

def print_routes(api):
	return Response(endpoints, mimetype="text/plain")

def print_invalid_route(api, path):
	return make_error(APIErrorType.INVALID_ROUTE), 404

def register_routes(api, objects):
	api.add_url_rule(
		"/api/upload_android_csv",
		"upload_android_csv",
		partial(upload_csv, api, objects["devices_importer"], OperatingSystem.ANDROID),
		methods=["GET", "POST"])
	api.add_url_rule(
		"/api/upload_ios_csv",
		"upload_ios_csv",
		partial(upload_csv, api, objects["devices_importer"], OperatingSystem.IOS),
		methods=["GET", "POST"])

	api.add_url_rule("/", "print_routes", partial(print_routes, api))
	api.add_url_rule("/<path:path>", "/<path:path>", partial(print_invalid_route, api))

	# api.register_error_handler(Exception, handle_api_exception)
