from pathlib import Path

from analysis.analyzer import AppAnalyzer
from model.app import OperatingSystem

class Permission_Analyzer(AppAnalyzer):
	
	def name(self):
		return 'Permission_Analyzer'
	
	def analyze_app(self, app):
		if app.os != OperatingSystem.ANDROID:
			raise ValueError("Only Android apps can be checked for permissions")

		# Currently google lists a total of 40 permissions marked as dangerous at https://developer.android.com/reference/android/Manifest.permission
		# This method simply checks how many are requested and then normalizes the score.
		dangerous_perm_total = 0
		p = Path(__file__).with_name('dangerous_permissions.txt')
		with p.open('r') as f:				
			for line in f:
				for permission in app.permissions:
					if permission in line:
						dangerous_perm_total += 1
					
		score = dangerous_perm_total / 40
		if(score > 1):
			score = 1
		return score
			
	# This method returns all of the dangerous permissions present in the application.
	def dangerous_permission_report(self, app):
		if app.os != OperatingSystem.ANDROID:
			raise ValueError("Only Android apps can be checked for permissions")
		
		dangerous_perm_list = []
		p = Path(__file__).with_name('dangerous_permissions.txt')
		with p.open('r') as f:				
			for line in f:
				for permission in app.permissions:
					if permission in line:
						dangerous_perm_list.append(permission)

		return dangerous_perm_list