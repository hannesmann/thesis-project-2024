# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

import logging

from datetime import datetime
from queue import Queue
from model.app import OperatingSystem
from sqlalchemy import Column, Enum, String, ForeignKey, UniqueConstraint
from threading import Thread, Timer

class ThreadEventType(Enum):
	STOP_THREAD = 0
	IMPORT_DATA = 1

class ThreadEvent:
	def __init__(self, type, data=None):
		self.type = type
		self.data = data

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

		self.events = Queue()
		self.thread = Thread(target=self.import_thread, daemon=True)
		self.thread.start()

	# Thread to periodically import data
	def import_thread(self):
		logger = logging.getLogger("app")
		logger.info(f"Importer thread started at {datetime.now():%Y-%m-%d %H:%M:%S}")

		while True:
			event = self.events.get()

			if event.type == ThreadEventType.IMPORT_DATA:
				importer = event.data
				next_fetch_time = importer.next_fetch_time()
				logger.info(f"Fetched data from {type(importer).__name__}")

				if next_fetch_time:
					next_fetch_secs = round((next_fetch_time - datetime.now()).total_seconds())
					logger.info(f"Next fetch in {next_fetch_secs}s")

					timer = Timer(next_fetch_secs, lambda:
				   		self.events.put(ThreadEvent(ThreadEventType.IMPORT_DATA, importer)))
					timer.start()
				else:
					logger.info(f"{type(importer).__name__} done")

			elif ThreadEventType.STOP_THREAD:
				return

	# Add a new importer and import from it immediately
	def add_importer(self, importer):
		self.events.put(ThreadEvent(ThreadEventType.IMPORT_DATA, importer))
