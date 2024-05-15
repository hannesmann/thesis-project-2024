# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

from bottle import response
from api.error import *

def define_fetch_routes(app, repositories):
	@app.route("/", method="GET")
	@app.route("/api/overview", method="GET")
	def overview():
		return make_success({
			"overview": {
				"apps": len(repositories.apps.apps),
				"devices": len(repositories.devices.devices)
			}
		})

	@app.route("/api/apps", method="GET")
	def list_apps():
		return make_success({
			"count": len(repositories.apps.apps),
			"apps": list(map(lambda a: a.__dict__, repositories.apps.apps.values()))
		})

	@app.route("/api/devices", method="GET")
	def list_devices():
		return make_success({
			"count": len(repositories.devices.devices),
			"devices": list(map(lambda d: d.__dict__, repositories.devices.devices.values()))
		})

	@app.route("/api/app/<os>/<id>", method="GET")
	def get_app_from_id(os, id):
		unique_id = ""
		if os == "android":
			unique_id = f"{id}_ANDROID"
		elif os == "ios":
			unique_id = f"{id}_IOS"

		if unique_id in repositories.apps.apps:
			return make_success({
				"data": repositories.apps.apps[unique_id].__dict__,
				"risk_score": repositories.apps.risk_scores.get(unique_id)
			})

		response.status = 404
		return make_error(ERROR_NOT_FOUND)

	@app.route("/api/device/<id>", method="GET")
	def get_device_from_id(id):
		if id in repositories.devices.devices:
			return make_success({"data": repositories.devices.devices[id].__dict__})

		response.status = 404
		return make_error(ERROR_NOT_FOUND)
