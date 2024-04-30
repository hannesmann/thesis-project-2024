# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

import abc
import logging

from datetime import datetime
from enum import Enum
from repository.apps import ApplicationRepository
from threading import Thread, Timer
from queue import Queue

class DeviceImporter(abc.ABC):
	"""Represents a source of devices and applications"""

	@abc.abstractmethod
	def	fetch_discovered_apps(self):
		"""Fetch a list of all discovered apps from this data source"""
		pass

	@abc.abstractmethod
	def	fetch_devices(self):
		"""Fetch a list of all devices from this data source"""
		pass

	@abc.abstractmethod
	def next_fetch_time(self):
		"""
		The next time the server should fetch from this data source
		If this method returns None, the data source has no more valid data
		and should be removed from the list of active importers
		"""
		pass

class ThreadEventType(Enum):
	STOP_THREAD = 0
	IMPORT_DATA = 1

class ThreadEvent:
	def __init__(self, type, data=None):
		self.type = type
		self.data = data

class DeviceImporterThread:
	"""Periodically imports data from DeviceImporters and saves it in repositories"""

	def __init__(self, application_repo, devices_repo):
		self.application_repo = application_repo
		self.devices_repo = devices_repo

		self.logger = logging.getLogger("app")

		self.events = Queue()
		self.thread = Thread(target=self.import_thread, daemon=True)

		self.thread.start()

	# Add a new importer and import from it immediately
	def add_importer(self, importer):
		self.events.put(ThreadEvent(ThreadEventType.IMPORT_DATA, importer))

	# Thread to periodically import data from managed devices
	def import_thread(self):
		self.logger.info(f"MDM importer thread started at {datetime.now():%Y-%m-%d %H:%M:%S}")

		while True:
			event = self.events.get()

			if event.type == ThreadEventType.IMPORT_DATA:
				importer = event.data

				for a in importer.fetch_discovered_apps():
					# TODO: Add count
					self.application_repo.add_or_update_app(a["info"])

				next_fetch_time = importer.next_fetch_time()
				self.logger.info(f"Fetched data from {type(importer).__name__}")

				if next_fetch_time:
					next_fetch_secs = round((next_fetch_time - datetime.now()).total_seconds())
					self.logger.info(f"Next fetch in {next_fetch_secs}s")

					next_fetch_timer = Timer(next_fetch_secs, lambda:
				   		self.events.put(ThreadEvent(ThreadEventType.IMPORT_DATA, importer)))
					next_fetch_timer.start()
				else:
					self.logger.info(f"{type(importer).__name__} done")

			elif ThreadEventType.STOP_THREAD:
				return
