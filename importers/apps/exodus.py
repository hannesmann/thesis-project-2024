# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

from loguru import logger
from importers.apps.importer import AppInfoImporter
from model.app import OperatingSystem

from ratelimit import limits, sleep_and_retry

import configs
import requests

class ExodusImporter(AppInfoImporter):
	def os(self):
		return OperatingSystem.ANDROID

	@sleep_and_retry
	@limits(calls=30, period=1)
	def import_info_for_app(self, app, repo):
		# Already analyzed
		if app.permissions and app.trackers:
			return

		# The Exodus API has occasionally given us trouble due to misconfigured caches on their end. Hopefully it keeps working.
		# For demonstration purposes it is probably a good idea to use some pre-fetched JSON to avoid making live calls to the API
		# in front of an audience.
		versionBlob = requests.get(
			f'https://reports.exodus-privacy.eu.org/api/search/{app.id}/details',
			headers = {'Authorization': f'Token {configs.secrets.api.exodus}'}
		)
		data = versionBlob.json()

		# Not found
		if len(data) == 0:
			logger.warning(f"App {app.id} not found in Exodus Privacy database")
			return

		# The reports are unordered so we need to iterate over them to find the most recent version. The bigger the versionCode, the more recent it is.
		# Note that the versionCode and versionName are different. The code is just an integer, while the name is the true versions like "460.0.0.34.89" as an example.
		permissions = []
		trackers = []
		appName = ''
		versionCode = 0
		versionName = ''

		for element in data:
			if(int(element['version_code']) > versionCode):
				appName = element['app_name']
				versionCode = int(element['version_code'])
				versionName = element['version_name']
				permissions = element['permissions']
				trackers = element['trackers']

		# Set the app attributes
		app.name = appName
		app.permissions = list(set(permissions))
		logger.info(f"Got {len(app.permissions)} permissions for {app.id}")
		app.trackers = list(set(trackers))
		logger.info(f"Got {len(app.trackers)} trackers for {app.id}")

		# Add to repo and return
		repo.add_or_update_app(app)
		return#

