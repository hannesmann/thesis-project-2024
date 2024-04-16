# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

import abc

class DataImporter(abc.ABC):
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
