# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

import abc
import logging

from datetime import datetime
from enum import Enum
import traceback
from repository.apps import ApplicationRepository
from threading import Thread, Timer
from queue import Queue

class AppAnalyzer(abc.ABC):
	"""Determines the risk score of an application using a certain metric (permissions, trackers, etc)"""

	@abc.abstractmethod
	def	name(self):
		"""Name that can be shown to an administrator when inspecting an app"""
		pass

	@abc.abstractmethod
	def	analyze_app(self, app):
		"""Analyze an app and return a risk score from 0.0 (0%) to 1.0 (100%)"""
		pass

class ThreadEventType(Enum):
	STOP_THREAD = 0
	ANALYZE_APPS = 1

class ThreadEvent:
	def __init__(self, type, data=None):
		self.type = type
		self.data = data

class AppAnalyzerThread:
	"""Periodically analyze apps and saves risk scores in ApplicationRepository"""

	def __init__(self, application_repo):
		self.application_repo = application_repo
		# TODO: Add the analyzers here (or an add analyzer method)
		self.analyzers = []
		self.logger = logging.getLogger("app")

		self.events = Queue()
		self.events.put(ThreadEvent(ThreadEventType.ANALYZE_APPS))

		self.thread = Thread(target=self.analysis_thread, daemon=True)
		self.thread.start()

	def add_analyzer(self, analyzer):
		self.logger.info(f"New app analyzer: {type(analyzer).__name__}")
		self.analyzers.append(analyzer)

	# Thread to periodically analyze apps
	def analysis_thread(self):
		self.logger.info(f"App analysis thread started at {datetime.now():%Y-%m-%d %H:%M:%S}")

		while True:
			event = self.events.get()

			if event.type == ThreadEventType.ANALYZE_APPS:
				for app in self.application_repo.apps.values():
					risk_score = 0.0

					for analyzer in self.analyzers:
						try:
							self.logger.info(f"{type(analyzer).__name__} ({analyzer.name()}) checking {app.id}")
							analyzer_score = analyzer.analyze_app(app)
							# TODO: Max value here instead of mean value?
							risk_score = (risk_score + analyzer_score) / 2.0
							self.logger.info(f"Risk score for {app.id} is now {risk_score}")
						except Exception:
							self.logger.error(f"Analyzer {type(analyzer).__name__} failed: {traceback.format_exc()}")

					self.application_repo.add_or_update_risk_score(app.unique_id(), risk_score)

				# TODO: Don't analyze every 15 secs
				next_analysis_timer = Timer(15, lambda:
					self.events.put(ThreadEvent(ThreadEventType.ANALYZE_APPS)))
				next_analysis_timer.start()

			elif ThreadEventType.STOP_THREAD:
				return
