# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

from munch import Munch, unmunchify

ERROR_UNKNOWN = "unknown"

ERROR_INVALID_ROUTE = "invalid_route"
ERROR_WRONG_METHOD = "wrong_method"
ERROR_NOT_FOUND = "not_found"

ERROR_CSV_PARSE_ERROR = "csv_parse_error"

def combine(a, b):
	if isinstance(b, dict):
		a.update(b)
	elif isinstance(b, Munch):
		a.update(unmunchify(b))
	elif b:
		a.update(vars(b))
	return a

def make_success(details=None):
	return combine({"status": "success"}, details)

def make_error(type, details=None):
	return combine({"status": "error", "error": type}, details)
