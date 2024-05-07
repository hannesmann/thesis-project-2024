import logging
import requests
from importers.apps.importer import AppInfoImporter
from model.app import OperatingSystem
from ratelimit import limits, sleep_and_retry
from bs4 import BeautifulSoup

class AppStoreImporter(AppInfoImporter):
	"""Imports store page URL and privacy policy URL from iTunes Search API"""

	def	os(self):
		return OperatingSystem.IOS

	# iTunes Search API is limited to 20 calls per minute
	@sleep_and_retry
	@limits(calls=20, period=60)
	def import_store_page_url(self, app):
		# TODO: set a user agent
		# headers = {"User-Agent": ""}
		res = requests.get(f"https://itunes.apple.com/lookup?bundleId={app.id}").json()
		# TODO: if res["resultCount"] == 0 => remove app
		if res["resultCount"] > 0 and res["results"][0]:
			return res["results"][0]["trackViewUrl"]
		return None

	# Since we are fetching from the App Store, limit to a low amount of requests
	@sleep_and_retry
	@limits(calls=1, period=5)
	def import_privacy_policy_url(self, app):
		res = requests.get(app.store_page_url).text
		page = BeautifulSoup(res, "html.parser")
		for link in page.find_all("a"):
			if link.get_text(strip=True).lower() == "privacy policy":
				return link.get("href")
		return None

	def	import_info_for_app(self, app, repo):
		logging.getLogger("app").info(f"AppStoreImporter checking {app.id}")
		if not app.store_page_url:
			app.store_page_url = self.import_store_page_url(app)
			if app.store_page_url:
				logging.getLogger("app").info(f"Found store page URL for {app.id}: {app.store_page_url}")
		if app.store_page_url and not app.privacy_policy_url:
			app.privacy_policy_url = self.import_privacy_policy_url(app)
			if app.privacy_policy_url:
				logging.getLogger("app").info(f"Found privacy page URL for {app.id}: {app.privacy_policy_url}")

		repo.add_or_update_app(app)
