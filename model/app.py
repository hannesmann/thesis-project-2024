# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

from enum import Enum
from urllib.parse import urlparse

class OperatingSystem(Enum):
	"""Enumeration of supported mobile operating systems"""

	ANDROID = 1
	IOS = 2

class Application:
	"""Represents a mobile application"""

	def __init__(self, id, os, name=None, permissions=None, store_page_url=None, privacy_policy_url=None):
		"""
		:param id: Application ID (Android), Bundle ID (iOS)
		:param os: Operating system this application was developed for
		:param name: English name of this application
		:param permissions: Permissions granted to this application
		:param store_page_url: Application store page
		:param privacy_policy_url: Privacy policy provided by the developer
		"""

		self.id = id
		self.os = os
		self.name = name
		self.permissions = permissions

		if store_page_url:
			self.store_page_url = urlparse(store_page_url)
		else:
			self.store_page_url = None

		if privacy_policy_url:
			self.privacy_policy_url = urlparse(privacy_policy_url)
		else:
			self.privacy_policy_url = None

	# TODO: Can this be determined through MDM?
	def is_system_app(self):
		return False

	def is_complete_app(self):
		"""Returns true if this app has all the information possible for this operating system"""

		if self.os == OperatingSystem.ANDROID:
			return self.name and len(self.permissions) > 0 and self.store_page_url and self.privacy_policy_url
		else:
			return self.name and self.store_page_url and self.privacy_policy_url
