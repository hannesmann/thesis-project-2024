# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

from datetime import datetime
from enum import Enum
from loguru import logger
from queue import Queue
from threading import Thread, Timer

import abc
import configs
import traceback

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

	def __init__(self, application_repo, devices_repo, default_analyzers=None):
		self.application_repo = application_repo
		self.devices_repo = devices_repo

		self.analyzers = []
		if configs.main.analysis.autorun and default_analyzers:
			logger.info(f"Adding app analysers: {" ".join([type(a).__name__ for a in default_analyzers])}")
			self.analyzers = default_analyzers

		self.events = Queue()
		self.events.put(ThreadEvent(ThreadEventType.ANALYZE_APPS))

		self.thread = Thread(target=self.analysis_thread, daemon=True)
		self.thread.start()

	# Thread to periodically analyze apps
	def analysis_thread(self):
		logger.success(f"App analysis thread started and waiting for events")

		while True:
			event = self.events.get()

			if event.type == ThreadEventType.ANALYZE_APPS:
				for app in filter(lambda a: not a.is_system_app(), self.application_repo.apps.values()):
					sources = {}

					for analyzer in self.analyzers:
						try:
							logger.info(f"{type(analyzer).__name__} ({analyzer.name()}) checking {app.id}")
							analyzer_score = analyzer.analyze_app(app)
							sources[analyzer.name()] = analyzer_score
						except Exception as e:
							if configs.main.server.debug:
								logger.warning(f"Analyzer {type(analyzer).__name__} failed for {app.id}: {traceback.format_exc()}")
							else:
								logger.warning(f"Analyzer {type(analyzer).__name__} failed for {app.id}: {e}")

					# Avoid updating the risk score if analysis couldn't be completed by any class
					if len(sources) > 0:
						self.application_repo.update_risk_score_from_sources(app, sources)

				self.devices_repo.update_risk_scores_from_repo(self.application_repo)

				next_analysis_timer = Timer(configs.main.analysis.timer, lambda:
					self.events.put(ThreadEvent(ThreadEventType.ANALYZE_APPS)))
				next_analysis_timer.start()

			elif ThreadEventType.STOP_THREAD:
				return
