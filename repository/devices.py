# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

import logging
from model.app import OperatingSystem
from model.mdm import Device, DeviceOwnership
from sqlalchemy import Column, Enum, String, ForeignKey, UniqueConstraint

class DevicesRepository:
	"""Stores information about devices and caches it in a database"""

	def __init__(self, db):
		"""
		:param db: SQLAlchemy database object
		"""
		self.db = db

		# Define tables for storing details about devices
		self.dt = db.Table(
			"devices",

			Column("id", String(255), primary_key=True),
			Column("name", String(255)),
			Column("os", Enum(OperatingSystem)),
			Column("ownership", Enum(DeviceOwnership)),
		)
		self.ddat = db.Table(
			"device_discovered_apps",

			Column("device_id", String(255), ForeignKey("devices.id")),
			Column("app_id", String(255)),

			UniqueConstraint("device_id", "app_id")
		)

		self.devices = {}
		self.logger = logging.getLogger("app")

	def add_or_replace_device(self, device):
		# Devices should always be replaced, they might not have some apps anymore
		self.devices[device.id] = device

	def load_tables(self):
		devices_in_db = self.db.session.execute(self.dt.select()).all()
		self.logger.info(f"Loaded {len(devices_in_db)} device(s) from database")

		for d in devices_in_db:
			mappings = d._mapping

			discovered_apps = set()
			discovered_apps_in_db = self.db.session.execute(self.ddat.select().where(self.ddat.columns.device_id == mappings["id"])).all()

			for	d in discovered_apps_in_db:
				discovered_apps.add(d._mapping["app_id"])

			device = Device(
				mappings["id"],
				mappings["name"],
				mappings["os"],
				mappings["ownership"])
			device.update_discovered_apps(discovered_apps)
			self.add_or_replace_device(device)

	def save_tables(self):
		exec = self.db.session.execute
		self.logger.info(f"Saving {len(self.devices)} device(s) to database")

		exec(self.dt.delete())
		for d in self.devices.values():
			exec(self.dt.insert().values(
				id = d.id,
				name = d.name,
				os = d.os,
				onwership = d.ownership
			))

			exec(self.ddat.delete().where(self.ddat.columns.device_id == d.id))
			for a in d.discovered_apps:
				exec(self.ddat.insert().values(device_id = d.id, app_id = a.id))

		self.db.session.commit()

