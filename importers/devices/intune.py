# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

from loguru import logger

import datetime
import msal
from munch import Munch
import requests
import configs
import model

from importers.devices.importer import DeviceImporter
from model.app import OperatingSystem, Application

intune_platforms = {
	"ios": OperatingSystem.IOS,
	"androidOSP": OperatingSystem.ANDROID,
	"androidDeviceAdministrator": OperatingSystem.ANDROID,
	"androidWorkProfile": OperatingSystem.ANDROID,
	"androidDedicatedAndFullyManaged": OperatingSystem.ANDROID
}

class IntuneImporter(DeviceImporter):
	def __init__(self):
		self.token = None
		self.last_fetch_time = None

	def connect(self):
		if configs.secrets.api.intune.secret:
			app = msal.ConfidentialClientApplication(
				authority=configs.secrets.api.intune.authority,
				client_id=configs.secrets.api.intune.client_id,
				client_credential=configs.secrets.api.intune.secret

				# TODO: Connect msal.SerializableTokenCache to database
				# token_cache=...
			)

			token_result = app.acquire_token_silent(scopes=configs.secrets.api.intune.scope, account=None)
			if not token_result:
				token_result = app.acquire_token_for_client(scopes=configs.secrets.api.intune.scope)

			if "access_token" in token_result:
				self.token = token_result["access_token"]
				logger.info(f"Connected to Intune: {self.token}")
			else:
				logger.error(f"Could not connect to Intune: {token_result.get("error")}")
				logger.error(token_result.get("error_description"))

	def intune_request(self, method, url):
		headers = {"Authorization": f"Bearer {self.token}"}
		res = requests.request(method, f"https://graph.microsoft.com/v1.0/{url}", headers=headers)
		return res.json()

	def	fetch_discovered_apps(self):
		if self.token:
			discovered_apps = self.intune_request("get", "deviceManagement/detectedApps")["value"]
			result = {}

			for app in discovered_apps:
				# Fix up the app ID
				app_id = app["displayName"].strip(". ")

				os = OperatingSystem.UNKNOWN
				if app["platform"] in intune_platforms:
					os = intune_platforms[app["platform"]]

				result[app_id] = Munch(
					info=Application(app_id, os),
					count=app["deviceCount"]
				)

			self.last_fetch_time = datetime.datetime.now()
			return result

		return {}

	def	fetch_devices(self):
		if self.token:
			self.last_fetch_time = datetime.datetime.now()
		return {}

	def next_fetch_time(self):
		if self.last_fetch_time:
			# TODO: Add timedelta to config
			return self.last_fetch_time + datetime.timedelta(days=1)
		elif self.token:
			return datetime.datetime.now()
		return None
