# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

from csv import reader
from importer import DataImporter
from model.app import Application

# TODO: Improve CSV format (add app name, etc) and convert existing dataset
class CSVImporter(DataImporter):
	"""CSV format: app;count;total devices"""

	def	__init__(self, filename, os):
		self.apps = {}

		with open(filename) as file:
			csv_reader = reader(file, delimiter=";")

			# Skip the first row
			for row in csv_reader[1:]:
				self.apps[row["app"]] = {
					"info": Application(row["app"], os),
					"count": int(row["count"])
				}

	def	fetch_discovered_apps(self):
		return self.apps

	def	fetch_devices(self):
		# TODO: CSV should be able to specify devices (apps.csv and devices.csv?)
		return {}

	def next_fetch_time(self):
		# CSV files don't need to be refreshed periodically
		return None
