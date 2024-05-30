# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

from loguru import logger

import datetime
import msal
import requests
import configs

from mergedeep import Strategy, merge
from munch import Munch
from ratelimit import sleep_and_retry, limits

from importers.devices.importer import DeviceImporter

from model.app import OperatingSystem, Application
from model.mdm import Device, DeviceOwnership

intune_supported_platforms = {
	"androidOSP": OperatingSystem.ANDROID,
	"androidDeviceAdministrator": OperatingSystem.ANDROID,
	"androidWorkProfile": OperatingSystem.ANDROID,
	"androidDedicatedAndFullyManaged": OperatingSystem.ANDROID,
	"ios": OperatingSystem.IOS,
}

intune_supported_operating_systems = {
	"Android": OperatingSystem.ANDROID,
	"iOS": OperatingSystem.IOS,
}

class IntuneImporter(DeviceImporter):
	def __init__(self):
		self.token = None
		self.last_fetch_time = None
		self.request_counter = 0

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

	@sleep_and_retry
	@limits(calls=20, period=10)
	def intune_request(self, method, url):
		headers = {"Authorization": f"Bearer {self.token}"}
		# NOTE: The beta API has to be used to get a list of apps for a specific device
		# The Intune portal uses the beta API
		next_link = f"https://graph.microsoft.com/beta/{url}"
		result = {}

		while next_link:
			self.request_counter += 1
			if configs.main.server.debug:
				logger.info(f"Sent {self.request_counter} requests to Graph")

			res = requests.request(method, next_link, headers=headers)
			current_result = res.json()
			result = merge({}, result, current_result, strategy=Strategy.ADDITIVE)

			next_link = current_result.get("@odata.nextLink")
			if next_link:
				if configs.main.server.debug:
					logger.info(f"Got more results from Graph: {next_link}")

		return result

	def	fetch_discovered_apps(self):
		if self.token:
			path = "deviceManagement/detectedApps?$select=displayName,platform,deviceCount"
			discovered_apps = self.intune_request("get", path)["value"]
			result = {}

			for app in discovered_apps:
				# Fix up the app ID
				app_id = app["displayName"].strip(". ")

				if app["platform"] in intune_supported_platforms:
					os = intune_supported_platforms[app["platform"]]
					result[app_id] = Munch(
						info=Application(app_id, os),
						count=app["deviceCount"]
					)
				else:
					logger.warning(f"Got app {app["displayName"]} for unknown platform: {app["platform"]}")

			self.last_fetch_time = datetime.datetime.now()
			return result

		return {}

	def	fetch_devices(self):
		if self.token:
			path = "deviceManagement/managedDevices?$select=operatingSystem,id,deviceName,managedDeviceOwnerType"
			discovered_devices = self.intune_request("get", path)["value"]
			result = {}

			# Fetch devices from Intune
			for device in discovered_devices:
				if device["operatingSystem"] in intune_supported_operating_systems:
					os = intune_supported_operating_systems[device["operatingSystem"]]
					ownership = DeviceOwnership.CORPORATE_OWNED
					if device["managedDeviceOwnerType"] == "personal":
						ownership = DeviceOwnership.USER_OWNED
					result[device["id"]] = Device(device["id"], device["deviceName"].replace(" ", "_"), os, ownership)

					# Fetch app device statuses and associate with our results
					path = f"deviceManagement/managedDevices/{device["id"]}/detectedApps?$select=displayName"
					discovered_device_apps = self.intune_request("get", path)["value"]
					for app in discovered_device_apps:
						result[device["id"]].update_discovered_apps([app["displayName"]], False)
				else:
					logger.warning(f"Got device {device["id"]} for unknown platform: {device["operatingSystem"]}")

			self.last_fetch_time = datetime.datetime.now()
			return result

		return {}

	def next_fetch_time(self):
		if self.last_fetch_time:
			# TODO: Add timedelta to config
			return self.last_fetch_time + datetime.timedelta(days=1)
		elif self.token:
			return datetime.datetime.now()
		return None
