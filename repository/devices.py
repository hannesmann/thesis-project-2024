# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

from loguru import logger
from model.app import OperatingSystem
from model.mdm import Device, DeviceOwnership
from sqlalchemy import *
from time import time

metadata = MetaData()

# Define tables for storing details about devices
devices = Table(
	"devices",
	metadata,

	Column("id", String(255), primary_key=True),
	Column("name", String(255)),
	Column("os", Enum(OperatingSystem)),
	Column("ownership", Enum(DeviceOwnership))
)
discovered_apps = Table(
	"device_discovered_apps",
	metadata,

	Column("device_id", String(255), ForeignKey("devices.id")),
	Column("app_id", String(255)),

	UniqueConstraint("device_id", "app_id")
)

class DevicesRepository:
	"""Stores information about devices and caches it in a database"""

	def __init__(self, conn):
		"""
		:param conn: SQLAlchemy database connection
		"""
		self.conn = conn
		self.devices = {}

	def add_or_replace_device(self, device):
		# Devices should always be replaced since complete information is always retrieved from MDM
		self.devices[device.id] = device

	def __enter__(self):
		# Create default tables
		metadata.create_all(self.conn)

		# Get a list of existing devices
		drows = self.conn.execute(devices.select()).all()
		logger.success(f"Loaded {len(drows)} device(s) from database")

		for drow in drows:
			device = Device(
				drow.id,
				drow.name,
				drow.os,
				drow.ownership
			)

			discovered_apps = list()
			# Read device_discovered_apps for existing discovered applications
			arows = self.conn.execute(discovered_apps.select().where(discovered_apps.columns.device_id == drow.id)).all()
			for	arow in arows:
				discovered_apps.add(arow.app_id)
			device.update_discovered_apps(discovered_apps)

			# Add device to repository
			self.add_or_replace_device(device)

	def __exit__(self, *args):
		# Devices are always deleted and recreated with INSERT
		self.conn.execute(devices.delete())
		for device in self.devices.values():
			self.conn.execute(devices.insert().values(
				id = device.id,
				name = device.name,
				os = device.os,
				ownership = device.ownership,
			))

			# Save discovered apps if applicable
			self.conn.execute(discovered_apps.delete().where(discovered_apps.columns.device_id == device.id))
			for app in device.discovered_apps:
				self.conn.execute(discovered_apps.insert().values(device_id = device.id, app_id = app.id))

		self.conn.commit()
		logger.success(f"Saved {len(self.devices)} device(s) to database")
