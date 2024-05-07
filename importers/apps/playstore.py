import logging
import requests
from importers.apps.importer import AppInfoImporter
from model.app import OperatingSystem
from ratelimit import limits, sleep_and_retry
from bs4 import BeautifulSoup

class PlayStoreImporter(AppInfoImporter):
	"""Imports store page URL and privacy policy URL from Play Store"""

	def	os(self):
		return OperatingSystem.ANDROID

	# Since we are fetching from the Play Store, limit to a low amount of requests
	@sleep_and_retry
	@limits(calls=1, period=5)
	def import_privacy_policy_url(self, app):
		res = requests.get(f"https://play.google.com/store/apps/datasafety?id={app.id}").text
		page = BeautifulSoup(res, "html.parser")
		for link in page.find_all("a"):
			if link.get_text(strip=True).lower() == "privacy policy":
				return link.get("href")
		return None

	def	import_info_for_app(self, app, repo):
		logging.getLogger("app").info(f"PlayStoreImporter checking {app.id}")
		if not app.store_page_url:
			# The Play Store URL is predictable based on the app ID
			app.store_page_url = f"https://play.google.com/store/apps/details?id={app.id}"
			logging.getLogger("app").info(f"Found store page URL for {app.id}: {app.store_page_url}")
		if app.store_page_url and not app.privacy_policy_url:
			app.privacy_policy_url = self.import_privacy_policy_url(app)
			if app.privacy_policy_url:
				logging.getLogger("app").info(f"Found privacy page URL for {app.id}: {app.privacy_policy_url}")

		repo.add_or_update_app(app)
