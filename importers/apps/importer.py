# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

from enum import Enum
from loguru import logger
from queue import Queue
from threading import Thread, Timer

import abc
import copy
import configs

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

	def __init__(self, application_repo, default_importers=None):
		self.application_repo = application_repo

		self.importers = []
		if configs.main.importers.autorun and default_importers:
			logger.info(f"Adding app info importers: {" ".join([type(i).__name__ for i in default_importers])}")
			self.importers = default_importers

		self.events = Queue()
		self.events.put(ThreadEvent(ThreadEventType.SCAN_APPS))

		self.thread = Thread(target=self.import_thread, daemon=True)
		self.thread.start()

	# Thread to periodically import data from app stores and related sources
	def import_thread(self):
		logger.success(f"App info importer thread started and waiting for events")

		while True:
			event = self.events.get()

			if event.type == ThreadEventType.SCAN_APPS:
				for a in self.application_repo.apps.values():
					# Don't check system apps or apps that we already have all info available for
					should_check_app = not a.is_complete_app() and not a.is_system_app()
					if should_check_app:
						for i in filter(lambda i: i.os() == a.os, self.importers):
							try:
								logger.info(f"{type(i).__name__} checking {a.id}")
								i.import_info_for_app(copy.deepcopy(a), self.application_repo)
							except Exception as e:
								logger.warning(f"Importer {type(i).__name__} failed: {e}")

				next_scan_timer = Timer(configs.main.importers.timer, lambda:
					self.events.put(ThreadEvent(ThreadEventType.SCAN_APPS)))
				next_scan_timer.start()

			elif ThreadEventType.STOP_THREAD:
				return
