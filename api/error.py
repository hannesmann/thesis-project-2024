# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

from enum import Enum

class APIErrorType(Enum):
	"""
	Error type returned by the REST API
	"""

	UNKNOWN = 1

	INVALID_ROUTE = 2
	WRONG_METHOD = 3

	PARSE_ERROR = 4

def make_success(details=None):
	if details:
		return {
			"status": "SUCCESS",
			"details": details
		}
	else:
		return {
			"status": "SUCCESS"
		}

def make_error(type, details=None):
	if details:
		return {
			"status": "ERROR",
			"error": type.name,
			"details": details
		}
	else:
		return {
			"status": "ERROR",
			"error": type.name
		}
