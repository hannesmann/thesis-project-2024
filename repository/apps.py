# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

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

			Column("app_id", String, ForeignKey("applications.id")),
			Column("permission", String),

			UniqueConstraint("app_id", "permission")
		)
		self.trackers_table = db.Table(
			"android_trackers",

			Column("app_id", String, ForeignKey("applications.id")),
			Column("tracker", String),

			UniqueConstraint("app_id", "tracker")
		)

# Initialized by app.py
application_repo_instance = None
