# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

import abc
import logging

from datetime import datetime
from enum import Enum
from repository.apps import ApplicationRepository
from threading import Thread, Timer
from queue import Queue

class AppInfoImporter(abc.ABC):
	"""Represents a source of additional application data (permissions, trackers, etc)"""

	@abc.abstractmethod
	def	os(self):
		"""Get the operating system that this importer provides application info for"""
		pass

	@abc.abstractmethod
	def	import_info_for_app(self, app, repo):
		"""
		Updates the application in the ApplicationRepository if possible
		This method can add a new app if, for example, an iOS app should be connected with an Android app
		"""
		pass

class ThreadEventType(Enum):
	STOP_THREAD = 0
	SCAN_APPS = 1

class ThreadEvent:
	def __init__(self, type, data=None):
		self.type = type
		self.data = data

class AppInfoImporterThread:
	"""Periodically imports data from AppInfoImporter and saves it in ApplicationRepository"""

	def __init__(self, application_repo):
		self.application_repo = application_repo
		# TODO: Add the importers here (or an add importer method)
		self.importers = []
		self.logger = logging.getLogger("app")

		self.events = Queue()
		self.thread = Thread(target=self.import_thread, daemon=True)

		self.thread.start()

	# Thread to periodically import data from app stores and related sources
	def import_thread(self):
		self.logger.info(f"App info importer thread started at {datetime.now():%Y-%m-%d %H:%M:%S}")

		while True:
			event = self.events.get()

			if event.type == ThreadEventType.SCAN_APPS:
				# TODO: Access from multiple threads?
				for a in self.application_repo.apps.values():
					if not a.is_complete_app():
						for i in filter(lambda i: i.os() == a.os, self.importers):
							i.import_info_for_app(a, self.application_repo)

				next_scan_timer = Timer(15, lambda:
					self.events.put(ThreadEvent(ThreadEventType.SCAN_APPS)))
				next_scan_timer.start()

			elif ThreadEventType.STOP_THREAD:
				return
