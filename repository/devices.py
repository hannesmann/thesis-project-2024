# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

from loguru import logger
from model.app import OperatingSystem
from model.mdm import Device, DeviceOwnership
from sqlalchemy import *
from time import time

import configs

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

# Define tables for storing details about risk scores
risk_scores = Table(
	"device_risk_scores",
	metadata,

	Column("device_id", String(255), ForeignKey("devices.id")),
	Column("combined_value", Double)
)

def combine_risk_scores(current, next):
	if configs.main.analysis.risk_score_method_device == "avg":
		return (current + next) / 2.0
	elif configs.main.analysis.risk_score_method_device == "max":
		return max(current, next)
	raise ValueError("Invalid configs.main.analysis.risk_score_method_device")

class DevicesRepository:
	"""Stores information about devices and caches it in a database"""

	def __init__(self, conn):
		"""
		:param conn: SQLAlchemy database connection
		"""
		self.conn = conn
		self.devices = {}
		self.risk_scores = {}

	def add_or_replace_device(self, device):
		# Devices should always be replaced since complete information is always retrieved from MDM
		self.devices[device.id] = device

	def update_risk_scores_from_repo(self, apps):
		# Reset scores
		self.risk_scores = {}

		for device in self.devices:
			if len(device.discovered_apps) > 0:
				combined_score = 0.0

				# Build an intersection of all apps that are both in the repo and device
				# We need to build a list with the format "org.app.x_ANDROID", "com.app.y_IOS", etc to find risk scores
				device_app_ids = map(lambda a: f"{a}_{device.os.name}", device.discovered_apps)
				analyzed_device_apps = set(apps.risk_scores.keys()).intersection(device_app_ids)
				for app in analyzed_device_apps:
					combined_score = combine_risk_scores(combined_score, apps[app])

				self.risk_scores[device.id] = combined_score
				logger.info(f"Updated risk score for device {device.id}: {combined_score} (from {analyzed_device_apps} apps)")


	def __enter__(self):
		# Create default tables
		metadata.create_all(self.conn)

		# Get a list of existing devices
		drows = self.conn.execute(devices.select()).all()
		logger.success(f"Loaded {len(drows)} devices from database")

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

			rrow = self.conn.execute(risk_scores.select().where(risk_scores.columns.device_id == device.id)).first()
			if rrow:
				# Retreive the combined score
				self.risk_scores[rrow.device_id] = rrow.combined_value


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

			# Risk scores are always deleted and recreated with INSERT
			self.conn.execute(risk_scores.delete().where(risk_scores.columns.device_id == device.id))

			if device.id in self.risk_scores:
				# Save the combined score
				self.conn.execute(risk_scores.insert().values(
					device_id = device.id,
					combined_value = self.risk_scores[device.id]
				))

		self.conn.commit()
		logger.success(f"Saved {len(self.devices)} devices to database")
