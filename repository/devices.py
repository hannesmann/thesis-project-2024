# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

from model.app import OperatingSystem
from model.mdm import DeviceOwnership
from sqlalchemy import Column, Enum, String, ForeignKey, UniqueConstraint

class DevicesRepository:
	"""Stores information about devices and caches it in a database"""

	def __init__(self, db):
		"""
		:param db: SQLAlchemy database object
		"""
		self.db = db

		# Define tables for storing details about devices
		self.devices_table = db.Table(
			"devices",

			Column("id", String(255), primary_key=True),
			Column("name", String(255)),
			Column("os", Enum(OperatingSystem)),
			Column("ownership", Enum(DeviceOwnership)),
		)
		self.device_discovered_apps_table = db.Table(
			"device_discovered_apps",

			Column("device_id", String(255), ForeignKey("devices.id")),
			Column("app_id", String(255)),

			UniqueConstraint("device_id", "app_id")
		)

# Initialized by app.py
devices_repo_instance = None
