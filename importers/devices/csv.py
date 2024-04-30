# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

import csv
from io import StringIO
from importers.devices.importer import DeviceImporter
from model.app import Application

class CSVImporter(DeviceImporter):
	"""CSV format: app;count;total devices"""

	def	__init__(self, text, os):
		self.apps = {}
		csv_reader = list(csv.DictReader(StringIO(text), delimiter=";"))

		# Skip the first row
		for row in csv_reader[1:]:
			self.apps[row["app"]] = {
				"info": Application(row["app"], os),
				"count": int(row["count"])
			}

	def	fetch_discovered_apps(self):
		return self.apps.values()

	def	fetch_devices(self):
		# TODO: CSV should be able to specify devices (apps.csv and devices.csv?)
		return {}

	def next_fetch_time(self):
		# CSV files don't need to be refreshed periodically
		return None
