import requests

from analysis.analyzer import AppAnalyzer

class TrackerAnalyzer(AppAnalyzer):
	def __init__(self, token):
		super().__init__()
		self.token = token

	def name(self):
		return 'Exodus Privacy Trackers'

	def analyze_app(self, app):

		# According Binns et al. the median number of trackers embedded in 1 000 000 investigated apps was 10. Q1 and Q3 were 5 and 18 respectively.
		# This is somewhat arbitrary, but for the time being we assume it is very undesirable to have apps in the upper quarter of total number of trackers.
		# We use a normalization with 0 as minimum and 18 as maximum: x = (value - min) / (max - min)
		try:
			tracker_total = len(app.trackers)

			score = tracker_total / 18

			if(score > 1):
				score = 1

			return score

		except Exception as e:
			print(e)
			return -1


	# This method return a detailed list of all the trackers present in the application.
	def tracker_report(self, app):

		trackerBlob = requests.get(f'https://reports.exodus-privacy.eu.org/api/trackers', headers = {'Authorization': f'Token {self.token}'})

		trackerData = trackerBlob.json()

		trackerlist = app.trackers

		reportlist = []

		for tracker in trackerlist:

			reportlist.append(trackerData['trackers'][tracker])

		return reportlist