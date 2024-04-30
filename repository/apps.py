# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

import logging

from model.app import Application, OperatingSystem
from sqlalchemy import Column, Enum, String, Double, ForeignKey, UniqueConstraint

class ApplicationRepository:
	"""Retreives information about applications from various sources and caches it in a database"""

	def __init__(self, db):
		"""
		:param db: SQLAlchemy database object
		"""
		self.db = db

		# Define tables for storing details about applications
		self.at = db.Table(
			"applications",

			# Applications are identifed by a combination of ID and OS
			Column("id", String(255), primary_key=True),
			Column("os", Enum(OperatingSystem), primary_key=True),

			Column("name", String(255)),
			Column("store_page_url", String(255)),
			Column("privacy_policy_url", String(255)),

			Column("other_os_id", String(255))
		)
		self.pt = db.Table(
			"android_permissions",

			Column("app_id", String(255), ForeignKey("applications.id")),
			Column("permission", String(128)),

			UniqueConstraint("app_id", "permission")
		)
		self.tt = db.Table(
			"android_trackers",

			Column("app_id", String(255), ForeignKey("applications.id")),
			Column("tracker", String(128)),

			UniqueConstraint("app_id", "tracker")
		)
		self.rst = db.Table(
			"risk_scores",
			Column("app_unique_id", String(255), primary_key=True),
			Column("risk_score", Double),
		)

		self.apps = {}
		# TODO: Add date
		self.risk_scores = {}
		self.logger = logging.getLogger("app")

	def add_or_update_app(self, app):
		# Merge existing app
		if app.unique_id() in self.apps:
			current = self.apps[app.unique_id()]
			if app.name:
				current.name = app.name
			# TODO: Replace here if not null?
			current.permissions = current.permissions.union(app.permissions)
			current.trackers = current.trackers.union(app.trackers)
			if app.store_page_url:
				current.store_page_url = app.store_page_url
			if app.privacy_policy_url:
				current.privacy_policy_url = app.privacy_policy_url
			if app.other_os_id:
				current.other_os_id = app.other_os_id
		# Add to the list
		else:
			self.apps[app.unique_id()] = app

	def add_or_update_risk_score(self, app_unique_id, risk_score):
		self.risk_scores[app_unique_id] = float(risk_score)

	def load_tables(self):
		apps_in_db = self.db.session.execute(self.at.select()).all()
		self.logger.info(f"Loaded {len(apps_in_db)} app(s) from database")

		for a in apps_in_db:
			mappings = a._mapping

			permissions = set()
			trackers = set()

			if mappings["os"] == OperatingSystem.ANDROID:
				permissions_in_db = self.db.session.execute(self.pt.select().where(self.pt.columns.app_id == mappings["id"])).all()
				trackers_in_db = self.db.session.execute(self.tt.select().where(self.tt.columns.app_id == mappings["id"])).all()

				for	p in permissions_in_db:
					permissions.add(p._mapping["permission"])
				for	t in trackers_in_db:
					trackers.add(t._mapping["tracker"])

			app = Application(
				mappings["id"],
				mappings["os"],
				mappings["name"],
				permissions,
				trackers,
				mappings["store_page_url"],
				mappings["privacy_policy_url"],
				mappings["other_os_id"])
			self.add_or_update_app(app)

			risk_score_in_db = self.db.session.execute(self.rst.select().where(self.rst.columns.app_unique_id == app.unique_id())).first()
			if risk_score_in_db:
				self.add_or_update_risk_score(app.unique_id(), risk_score_in_db)

	def save_tables(self):
		exec = self.db.session.execute
		self.logger.info(f"Saving {len(self.apps)} app(s) to database")

		for a in self.apps.values():
			in_database = exec(self.at.select().where(self.at.columns.id == a.id)).first() is not None

			if in_database:
				exec(self.at.update().where(self.at.columns.id == a.id).values(
					name = a.name,
					store_page_url = a.store_page_url,
					privacy_policy_url = a.privacy_policy_url,
					other_os_id = a.other_os_id
				))
			else:
				exec(self.at.insert().values(
					id = a.id,
					os = a.os,
					name = a.name,
					store_page_url = a.store_page_url,
					privacy_policy_url = a.privacy_policy_url,
					other_os_id = a.other_os_id
				))

			if a.os == OperatingSystem.ANDROID:
				exec(self.pt.delete().where(self.pt.columns.app_id == a.id))
				for p in a.permissions:
					exec(self.pt.insert().values(app_id = a.id, permission = p))

				exec(self.tt.delete().where(self.tt.columns.app_id == a.id))
				for t in a.trackers:
					exec(self.tt.insert().values(app_id = a.id, tracker = t))

			risk_score = self.risk_scores[a.unique_id()]
			if risk_score:
				exec(self.rst.delete().where(self.rst.columns.app_unique_id == a.unique_id()))
				exec(self.rst.insert().values(app_unique_id = a.unique_id(), risk_score = risk_score))

		self.db.session.commit()

