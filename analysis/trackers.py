# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

import requests
import configs

from analysis.analyzer import AppAnalyzer
from model.app import OperatingSystem

class TrackerAnalyzer(AppAnalyzer):
	def name(self):
		return 'Exodus Privacy Trackers'

	def analyze_app(self, app):
		if app.os != OperatingSystem.ANDROID:
			raise ValueError("Only Android apps can be checked for trackers")

		# According Binns et al. the median number of trackers embedded in 1 000 000 investigated apps was 10. Q1 and Q3 were 5 and 18 respectively.
		# This is somewhat arbitrary, but for the time being we assume it is very undesirable to have apps in the upper quarter of total number of trackers.
		# We use a normalization with 0 as minimum and 18 as maximum: x = (value - min) / (max - min)
		tracker_total = len(app.trackers)

		score = tracker_total / 18

		if(score > 1):
			score = 1

		return score


	# This method return a detailed list of all the trackers present in the application.
	def tracker_report(self, app):

		trackerBlob = requests.get(f'https://reports.exodus-privacy.eu.org/api/trackers', headers = {'Authorization': f'Token {configs.secrets.api.exodus}'})

		trackerData = trackerBlob.json()

		trackerlist = app.trackers

		reportlist = []

		for tracker in trackerlist:

			reportlist.append(trackerData['trackers'][tracker])

		return reportlist
