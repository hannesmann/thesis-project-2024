# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

from pathlib import Path

import configs
from analysis.analyzer import AppAnalyzer
from model.app import OperatingSystem

class PermissionsAnalyzer(AppAnalyzer):
	def name(self):
		return 'Android Permissions'

	def analyze_app(self, app):
		if app.os != OperatingSystem.ANDROID:
			raise ValueError("Only Android apps can be checked for permissions")

		# Currently google lists a total of 40 permissions marked as dangerous at https://developer.android.com/reference/android/Manifest.permission
		# This method simply checks how many are requested and then normalizes the score.
		dangerous_perm_total = 0
		for line in configs.main.analysis.permissions.dangerous_permissions:
			for permission in app.permissions:
				if permission in line:
					dangerous_perm_total += 1

		score = dangerous_perm_total / len(configs.main.analysis.permissions.dangerous_permissions)
		if(score > 1):
			score = 1
		return score

	# This method returns all of the dangerous permissions present in the application.
	def dangerous_permission_report(self, app):
		if app.os != OperatingSystem.ANDROID:
			raise ValueError("Only Android apps can be checked for permissions")

		dangerous_perm_list = []
		for line in configs.main.analysis.permissions.dangerous_permissions:
			for permission in app.permissions:
				if permission in line:
					dangerous_perm_list.append(permission)

		return dangerous_perm_list
