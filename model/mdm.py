# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

from enum import Enum
from time import time

class DeviceOwnership(str, Enum):
	"""
	Ownership of device in MDM environment
	This setting determines the app list available to the server
	"""

	CORPORATE_OWNED = "corporate_owned"
	USER_OWNED = "user_owned"

class Device:
	"""Represents a managed user device"""

	def __init__(self, id, name, os, ownership):
		"""
		:param id: Unique ID of this device (example: "446925a3-64b7-4d7e-9e6e-0f9ab11b31d9")
		:param name: Name of this device (example: "Hannes_AndroidEnterprise_1/1/2024_9:00 AM")
		:param os: Operating system used on this device
		:param ownership: Determines if this device is corporate-owned or user-owned
		"""

		self.id = id
		self.name = name
		self.os = os
		self.ownership = ownership
		self.discovered_apps = list()

	def update_discovered_apps(self, apps, replace=True):
		"""
		:param apps: Discovered apps from a data source such as MDM
		:type apps: list or set
		:param replace: If set to true, the existing set of discovered apps will be cleared
		"""

		if replace:
			self.discovered_apps = list()

		for app in apps:
			# List of model.Application
			if hasattr(app, "package_id") and app.package_id not in self.discovered_apps:
				self.discovered_apps.add(app.package_id)
			# List of application package IDs
			elif isinstance(app, str) and app not in self.discovered_apps:
				self.discovered_apps.add(app)
			else:
				raise TypeError("Discovered apps should be a list of model.Application or package IDs")

	def is_app_installed(self, package_id):
		"""
		:param package_id: Application package ID
		"""
		return self.discovered_apps[package_id]

	def has_user_apps(self):
		"""
		Determines if all apps on the device, including user apps, have been discovered
		Only corporate-owned devices allow access to the user profile
		"""
		return self.ownership == DeviceOwnership.CORPORATE_OWNED and len(self.discovered_apps) > 0
