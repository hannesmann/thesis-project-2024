# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

import abc
import configs
import datetime

from enum import Enum
from repository.apps import ApplicationRepository
from threading import Thread, Timer
from queue import Queue
from loguru import logger

class DeviceImporter(abc.ABC):
	"""Represents a source of devices and applications"""

	@abc.abstractmethod
	def	connect(self):
		"""Connect to external service if necessary"""
		pass

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

	def __init__(self, application_repo, devices_repo, default_importers=None):
		self.application_repo = application_repo
		self.devices_repo = devices_repo

		self.events = Queue()
		if default_importers and configs.main.importers.autorun:
			for importer in default_importers:
				self.queue_import(importer)

		self.thread = Thread(target=self.import_thread, daemon=True)

		self.thread.start()

	# Start a timer to add an importer to the queue
	def delayed_import(self, importer, delay):
		next_fetch_timer = Timer(delay, lambda:
			self.events.put(ThreadEvent(ThreadEventType.IMPORT_DATA, importer)))
		next_fetch_timer.start()

	# Add new importer to queue
	def queue_import(self, importer):
		importer.connect()
		next_fetch_time = importer.next_fetch_time()
		if next_fetch_time:
			delay = abs(round((next_fetch_time - datetime.datetime.now()).total_seconds()))
			logger.info(f"Importer {type(importer).__name__} will be added in {datetime.timedelta(seconds=delay)}")
			self.delayed_import(importer, delay)
		else:
			self.events.put(ThreadEvent(ThreadEventType.IMPORT_DATA, importer))

	# Thread to periodically import data from managed devices
	def import_thread(self):
		logger.success(f"MDM importer thread started and waiting for events")

		while True:
			event = self.events.get()

			if event.type == ThreadEventType.IMPORT_DATA:
				importer = event.data

				for app in importer.fetch_discovered_apps():
					# TODO: Add count
					self.application_repo.add_or_update_app(app.info)

				next_fetch_time = importer.next_fetch_time()
				logger.info(f"Fetched data from {type(importer).__name__}")

				if next_fetch_time:
					delay = abs(round((next_fetch_time - datetime.datetime.now()).total_seconds()))
					logger.info(f"Next fetch for {type(importer).__name__} in {datetime.timedelta(seconds=delay)}")
					self.delayed_import(importer, delay)
				else:
					logger.info(f"{type(importer).__name__} done")

			elif ThreadEventType.STOP_THREAD:
				return
