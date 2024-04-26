# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

from enum import Enum

class APIErrorType(Enum):
	"""
	Error type returned by the REST API
	"""

	UNKNOWN = 1

class APIError():
	"""Represents an error that occured in the application"""

	def __init__(self, type, details=None):
		"""
		:param type: Error type
		:param details: Optional error details
		"""

		self.error = type
		if details:
			self.details = details
