# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

from loguru import logger
from model.app import Application, OperatingSystem
from sqlalchemy import *

import configs

metadata = MetaData()

# Define tables for storing details about applications
apps = Table(
	"apps",
	metadata,

	# Applications are identifed by a combination of ID and OS
	Column("id", String(255), primary_key=True),
	Column("os", Enum(OperatingSystem), primary_key=True),

	Column("name", String(255)),
	Column("store_page_url", String(255)),
	Column("privacy_policy_url", String(255)),

	Column("other_os_id", String(255))
)
permissions = Table(
	"android_permissions",
	metadata,

	Column("app_id", String(255), ForeignKey("apps.id")),
	Column("permission", String(128)),

	UniqueConstraint("app_id", "permission")
)
trackers = Table(
	"android_trackers",
	metadata,

	Column("app_id", String(255), ForeignKey("apps.id")),
	Column("tracker", String(128)),

	UniqueConstraint("app_id", "tracker")
)

# Define tables for storing details about risk scores
risk_scores = Table(
	"app_risk_scores",
	metadata,

	Column("app_unique_id", String(255), primary_key=True),
	Column("overall_value", Double),
	Column("method", String(32))
)
detailed_risk_scores = Table(
	"detailed_app_risk_scores",
	metadata,

	Column("app_unique_id", String(255), primary_key=True),
	Column("analyzer", String(255), primary_key=True),
	Column("value", Double),
)

class ApplicationRiskScore:
	def __init__(self, value, sources, method):
		self.overall_score = value
		self.sources = sources
		self.method = method

def combine_risk_scores(current, next):
	if not current:
		return next
	if configs.main.analysis.risk_score_method_app == "avg":
		return (current + next) / 2.0
	elif configs.main.analysis.risk_score_method_app == "max":
		return max(current, next)
	raise ValueError("Invalid configs.main.analysis.risk_score_method_app")

class ApplicationRepository:
	"""Retreives information about applications from various sources and caches it in a database"""

	def __init__(self, conn):
		"""
		:param conn: SQLAlchemy database connection
		"""
		self.conn = conn
		self.apps = {}
		self.risk_scores = {}

	def add_or_update_app(self, app):
		# Merge existing app
		if app.unique_id() in self.apps:
			current = self.apps[app.unique_id()]
			current.name = app.name or current.name
			current.permissions = app.permissions or current.permissions
			current.trackers = app.trackers or current.trackers
			current.store_page_url = app.store_page_url or current.store_page_url
			current.privacy_policy_url = app.privacy_policy_url or current.privacy_policy_url
			current.other_os_id = app.other_os_id or current.other_os_id
		# Add to the list
		else:
			self.apps[app.unique_id()] = app

	def update_risk_score_from_sources(self, app, sources):
		overall_score = None
		for source in sources:
			overall_score = combine_risk_scores(overall_score, sources[source])

		self.risk_scores[app.unique_id()] = ApplicationRiskScore(
			overall_score,
			sources,
			configs.main.analysis.risk_score_method_app
		)

		logger.info(f"Updated risk score for app {app.id}: {int(overall_score * 100)}% (from {len(sources)} sources)")

	def __enter__(self):
		# Create default tables
		metadata.create_all(self.conn)

		# Get a list of existing applications
		arows = self.conn.execute(apps.select()).all()
		logger.success(f"Loaded {len(arows)} apps from database")

		for arow in arows:
			pset = set()
			tset = set()

			# Read android_permissions and android_trackers if this is an Android app
			if arow.os == OperatingSystem.ANDROID:
				prows = self.conn.execute(permissions.select().where(permissions.columns.app_id == arow.id)).all()
				trows = self.conn.execute(trackers.select().where(trackers.columns.app_id == arow.id)).all()
				for	prow in prows:
					pset.add(prow.permission)
				for	trow in trows:
					tset.add(trow.tracker)

			app = Application(
				arow.id,
				arow.os,
				arow.name,
				pset,
				tset,
				arow.store_page_url,
				arow.privacy_policy_url,
				arow.other_os_id
			)
			# Add application to repository
			self.add_or_update_app(app)

			# Check if risk score has been saved for this application
			rrow = self.conn.execute(risk_scores.select().where(risk_scores.columns.app_unique_id == app.unique_id())).first()
			if rrow:
				sources = {}

				# Fetch a list of scores from analyzers
				drows = self.conn.execute(detailed_risk_scores.select().where(detailed_risk_scores.columns.app_unique_id == app.unique_id())).all()
				for drow in drows:
					sources[drow.analyzer] = drow.value

				# Retreive the overall and detailed scores
				self.risk_scores[app.unique_id()] = ApplicationRiskScore(
					rrow.overall_value,
					sources,
					rrow.method
				)


	def __exit__(self, *args):
		# Applications are always deleted and recreated with INSERT
		self.conn.execute(apps.delete())
		for app in self.apps.values():
			self.conn.execute(apps.insert().values(
				id = app.id,
				os = app.os,
				name = app.name,
				store_page_url = app.store_page_url,
				privacy_policy_url = app.privacy_policy_url,
				other_os_id = app.other_os_id
			))

			# Save to android_permissions and android_trackers if applicable
			if app.os == OperatingSystem.ANDROID:
				self.conn.execute(permissions.delete().where(permissions.columns.app_id == app.id))
				for permission in app.permissions or []:
					self.conn.execute(permissions.insert().values(app_id = app.id, permission = permission))

				self.conn.execute(trackers.delete().where(trackers.columns.app_id == app.id))
				for tracker in app.trackers or []:
					self.conn.execute(trackers.insert().values(app_id = app.id, tracker = tracker))

			# Risk scores are always deleted and recreated with INSERT
			self.conn.execute(risk_scores.delete().where(risk_scores.columns.app_unique_id == app.unique_id()))
			self.conn.execute(detailed_risk_scores.delete().where(detailed_risk_scores.columns.app_unique_id == app.unique_id()))

			# Save risk score if applicable
			if app.unique_id() in self.risk_scores:
				risk_score = self.risk_scores[app.unique_id()]

				# Save the overall score and method
				self.conn.execute(risk_scores.insert().values(
					app_unique_id = app.unique_id(),
					overall_value = risk_score.overall_score,
					method = risk_score.method
				))

				# Save all sources
				for source in risk_score.sources:
					self.conn.execute(detailed_risk_scores.insert().values(
						app_unique_id = app.unique_id(),
						analyzer = source,
						value = risk_score.sources[source]
					))

		self.conn.commit()
		logger.success(f"Saved {len(self.apps)} apps to database")

