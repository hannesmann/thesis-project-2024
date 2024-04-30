# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

import logging

from datetime import datetime
from model.app import Application, OperatingSystem
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
			Column("privacy_policy_url", String(255)),

			Column("other_os_id", String(255))
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

		self.apps = {}
		self.logger = logging.getLogger("app")

	def add_or_update_app(self, app):
		# Merge existing app
		if app.id in self.apps:
			if app.name:
				self.apps[app.id].name = app.name
			self.apps[app.id].permissions = self.apps[app.id].permissions.union(app.permissions)
			self.apps[app.id].trackers = self.apps[app.id].trackers.union(app.trackers)
			if app.store_page_url:
				self.apps[app.id].store_page_url = app.store_page_url
			if app.privacy_policy_url:
				self.apps[app.id].privacy_policy_url = app.privacy_policy_url
			if app.other_os_id:
				self.apps[app.id].other_os_id = app.other_os_id
		# Add to the list
		else:
			self.apps[app.id] = app

	def load_tables(self):
		apps_in_db = self.db.session.execute(self.applications_table.select()).all()
		self.logger.info(f"Loaded {len(apps_in_db)} app(s) from database")

		for a in apps_in_db:
			mappings = a._mapping

			# TODO: Permissions
			self.add_or_update_app(Application(
				mappings["id"],
				mappings["os"],
				mappings["name"],
				None,
				None,
				mappings["store_page_url"],
				mappings["privacy_policy_url"],
				mappings["other_os_id"]))

	def save_tables(self):
		exec = self.db.session.execute
		table = self.applications_table
		self.logger.info(f"Saving {len(self.apps)} app(s) to database")

		for a in self.apps.values():
			in_database = exec(table.select().where(table.columns.id == a.id)).first() is not None

			if in_database:
				exec(table.update().where(table.columns.id == a.id).values(
					name = a.name,
					store_page_url = a.store_page_url,
					privacy_policy_url = a.privacy_policy_url,
					other_os_id = a.other_os_id
				))
			else:
				exec(table.insert().values(
					id = a.id,
					os = a.os,
					name = a.name,
					store_page_url = a.store_page_url,
					privacy_policy_url = a.privacy_policy_url,
					other_os_id = a.other_os_id
				))

		self.db.session.commit()

