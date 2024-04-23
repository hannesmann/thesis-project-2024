# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

import abc

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
