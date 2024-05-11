import logging
import requests

from importers.apps.importer import AppInfoImporter
from model.app import OperatingSystem

from ratelimit import limits, sleep_and_retry

class ExodusImporter(AppInfoImporter):
	def __init__(self, token):
		super().__init__()
		self.token = token

	def os(self):
		return OperatingSystem.ANDROID

	@sleep_and_retry
	@limits(calls=30, period=1)
	def import_info_for_app(self, app, repo):
		logging.getLogger("app").info(f"ExodusImporter checking {app.id}")

		# TODO: Apps can have zero trackers
		if len(app.permissions) > 0 and len(app.trackers) > 0:
			return

		# The Exodus API has occasionally given us trouble due to misconfigured caches on their end. Hopefully it keeps working.
		# For demonstration purposes it is probably a good idea to use some pre-fetched JSON to avoid making live calls to the API
		# in front of an audience.
		versionBlob = requests.get(f'https://reports.exodus-privacy.eu.org/api/search/{app.id}/details', headers = {'Authorization': f'Token {self.token}'})
		data = versionBlob.json()

		# The reports are unordered so we need to iterate over them to find the most recent version. The bigger the versionCode, the more recent it is.
		# Note that the versionCode and versionName are different. The code is just an integer, while the name is the true versions like "460.0.0.34.89" as an example.
		permissions = []
		trackers = []
		versionCode = 0
		versionName = ''

		for element in data:
			if(int(element['version_code']) > versionCode):
				versionCode = int(element['version_code'])
				versionName = element['version_name']
				permissions = element['permissions']
				trackers = element['trackers']

		# Set the app attributes
		app.permissions = set(permissions)
		logging.getLogger("app").info(f"Got {len(app.permissions)} permission(s) for {app.id}")
		app.trackers = set(trackers)
		logging.getLogger("app").info(f"Got {len(app.trackers)} tracker(s) for {app.id}")

		# Add to repo and return
		repo.add_or_update_app(app)
		return

