import logging
import requests
from importers.apps.importer import AppInfoImporter
from model.app import OperatingSystem
from ratelimit import limits, sleep_and_retry
from bs4 import BeautifulSoup

language_header = {"Accept-Language": "en-US,en"}

@sleep_and_retry
@limits(calls=1, period=1)
def find_printable_privacy_policy_url(url):
	"""Attempts to find the printable version of a privacy policy through various heuristics"""

	# Check if there is a printable version (found on facebook.com)
	res_current = requests.get(url, headers=language_header)
	res_printable = requests.get(res_current.url.split("?")[0].strip("/ ") + "/printable", headers=language_header)

	if res_current.text != res_printable.text and res_printable.status_code == 200:
		return res_printable.url

	# TODO: Check for ?PrintView=true (microsoft.com)
	# Page hash is the same, seems to be running in JavaScript
	return url

class AppStoreImporter(AppInfoImporter):
	"""Imports store page URL and privacy policy URL from iTunes Search API"""

	def	os(self):
		return OperatingSystem.IOS

	# iTunes Search API is limited to 20 calls per minute
	@sleep_and_retry
	@limits(calls=20, period=60)
	def import_store_page_url(self, app):
		res = requests.get(f"https://itunes.apple.com/lookup?bundleId={app.id}").json()
		# TODO: if res["resultCount"] == 0 => remove app
		if res["resultCount"] > 0 and res["results"][0]:
			return res["results"][0]["trackViewUrl"]
		return None

	# Since we are fetching from the App Store, limit to a low amount of requests
	@sleep_and_retry
	@limits(calls=1, period=5)
	def import_privacy_policy_url(self, app):
		res = requests.get(app.store_page_url, headers=language_header).text
		page = BeautifulSoup(res, "html.parser")
		for link in page.find_all("a"):
			text = link.get_text(strip=True).lower()
			if "privacy policy" in text and "developer" in text:
				return find_printable_privacy_policy_url(link.get("href"))
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

class PlayStoreImporter(AppInfoImporter):
	"""Imports store page URL and privacy policy URL from Play Store"""

	def	os(self):
		return OperatingSystem.ANDROID

	# Since we are fetching from the Play Store, limit to a low amount of requests
	@sleep_and_retry
	@limits(calls=1, period=5)
	def import_privacy_policy_url(self, app):
		res = requests.get(f"https://play.google.com/store/apps/datasafety?id={app.id}", headers=language_header).text
		page = BeautifulSoup(res, "html.parser")
		for link in page.find_all("a"):
			if link.get_text(strip=True).lower() == "privacy policy" and "developer" in link.parent.get_text(strip=True).lower():
				return find_printable_privacy_policy_url(link.get("href"))
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
