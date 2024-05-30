# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

from enum import Enum
import configs

class OperatingSystem(str, Enum):
	"""Enumeration of supported mobile operating systems"""

	UNKNOWN = "unknown"
	ANDROID = "android"
	IOS = "ios"

class Application:
	"""Represents a mobile application"""

	def __init__(self, id, os, name=None, permissions=None, trackers=None, store_page_url=None, privacy_policy_url=None, other_os_id=None):
		"""
		:param id: Application ID (Android), Bundle ID (iOS)
		:param os: Operating system this application was developed for
		:param name: English name of this application

		:param permissions: Permissions granted to this application
		:param trackers: Trackers identified in the application

		:param store_page_url: Application store page
		:param privacy_policy_url: Privacy policy provided by the developer

		:param other_os_id: Application ID for this app on the other operating system (IOS=>ANDROID, ANDROID=>IOS)
		"""

		self.id = id
		self.os = os
		self.name = name

		self.permissions = None
		if permissions:
			self.permissions = set()
			for permission in permissions:
				self.permissions.add(permission)
			# Convert to list to make json.dump happy
			self.permissions = list(self.permissions)

		self.trackers = None
		if trackers:
			self.trackers = set()
			for tracker in trackers:
				self.trackers.add(tracker)
			self.trackers = list(self.trackers)

		self.store_page_url = store_page_url
		self.privacy_policy_url = privacy_policy_url

		self.other_os_id = other_os_id

	def is_system_app(self):
		if self.os == OperatingSystem.ANDROID:
			return self.id.lower() in configs.main.analysis.system_apps.android
		elif self.os == OperatingSystem.IOS:
			return self.id.lower() in configs.main.analysis.system_apps.ios
		return False

	def is_complete_app(self):
		"""Returns true if this app has all the information possible for this operating system"""

		if self.os == OperatingSystem.ANDROID:
			return self.name and len(self.permissions) > 0 and len(self.trackers) > 0 and self.store_page_url and self.privacy_policy_url
		else:
			return self.name and self.store_page_url and self.privacy_policy_url

	def unique_id(self):
		"""Return a unique ID across operating systems"""
		return f"{self.id}_{self.os.name}"
