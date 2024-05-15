# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

import toml

from munch import Munch, munchify
from os import path
from loguru import logger

main = Munch()
secrets = Munch()

def load(main_file, secrets_file):
	"""Load configs and store in configs.main, configs.secrets"""
	global main, secrets

	logger.info(f"Main config file: {main_file}")
	logger.info(f"Secrets file: {secrets_file}")

	if not path.exists(main_file):
		logger.critical(f"Config file {main_file} not found")
		return False

	if not path.exists(secrets_file):
		logger.critical(f"Secrets file {secrets_file} not found")
		return False

	main = munchify(toml.load(main_file))
	secrets = munchify(toml.load(secrets_file))

	if not secrets.api.openai:
		logger.critical("secrets.api.openai is not set. The GPT analyzer needs access to the OpenAI API to function.")
		return False

	if not secrets.api.exodus:
		logger.warning("secrets.api.exodus is not set. The Exodus Privacy API will not be used for fetching permissions and trackers.")

	return True
