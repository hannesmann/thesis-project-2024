# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

import logging

from datetime import datetime
from model.app import OperatingSystem
from sqlalchemy import Column, Enum, String, ForeignKey, UniqueConstraint

class ApplicationRepository:
	"""Retreives information about applications from various sources and caches it in a database"""

	def __init__(self, db):
		"""
		:param db: SQLAlchemy database object
		"""
		self.db = db

		# Define tables for storing details about applications
		self.applications_table = db.Table(
			"applications",

			# Applications are identifed by a combination of ID and OS
			Column("id", String(255), primary_key=True),
			Column("os", Enum(OperatingSystem), primary_key=True),

			Column("name", String(255)),
			Column("store_page_url", String(255)),
			Column("privacy_policy_url", String(255))
		)
		self.permissions_table = db.Table(
			"android_permissions",

			Column("app_id", String(255), ForeignKey("applications.id")),
			Column("permission", String(128)),

			UniqueConstraint("app_id", "permission")
		)
		self.trackers_table = db.Table(
			"android_trackers",

			Column("app_id", String(255), ForeignKey("applications.id")),
			Column("tracker", String(128)),

			UniqueConstraint("app_id", "tracker")
		)

		self.logger = logging.getLogger("app")

		# Run app scanner immediately
		self.scan_timer()

	# Timer to periodically scan for additional application data such as permissions and store page URLs
	def scan_timer(self):
		self.logger.info(f"App scanner started at {datetime.now():%Y-%m-%d %H:%M:%S}")
		# TODO: Increase timeout
		next_scan_timer = Timer(15, self.scan_timer)
		next_scan_timer.start()
