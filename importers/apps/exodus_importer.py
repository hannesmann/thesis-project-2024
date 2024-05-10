import requests

from importers.apps.importer import AppInfoImporter
from model.app import OperatingSystem

class ExodusInfoImporter(AppInfoImporter):
	def __init__(self, token):
		self.token = token

	def os(self):
		return OperatingSystem.ANDROID

	def import_info_for_app(self, app, repo):
		# The Exodus API has occasionally given us trouble due to misconfigured caches on their end. Hopefully it keeps working.
		# For demonstration purposes it is probably a good idea to use some pre-fetched JSON to avoid making live calls to the API
		# in front of an audience.
		versionBlob = requests.get('https://reports.exodus-privacy.eu.org/api/search/' + app.id + '/details', headers = {'Authorization': f'Token {self.token}'})
		data = versionBlob.json()

		# Backup the app in case of an exception
		backup = app

		# The reports are unordered so we need to iterate over them to find the most recent version. The bigger the versionCode, the more recent it is.
		# Note that the versionCode and versionName are different. The code is just an integer, while the name is the true versions like "460.0.0.34.89" as an example.
		try:
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
			app.permissions = permissions
			app.trackers = trackers

			# Add to repo and return
			repo.add_or_update_app(app)
			return

		except Exception as e:
			app = backup
			print("ERROR IN EXODUS_INFO_IMPORTER:")
			print(e)
			return

