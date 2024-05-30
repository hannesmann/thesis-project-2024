# Copyright (c) 2024 Hannes Mann, Alexander Wigren
# See LICENSE for details

from analysis.gpt import GPTAnalyzer
from analysis.permissions import PermissionsAnalyzer
from analysis.trackers import TrackerAnalyzer
from importers.apps.exodus import ExodusImporter
from importers.apps.urls import AppStoreImporter, PlayStoreImporter
from importers.devices.intune import IntuneImporter

default_config_file = "config.toml"
default_secrets_file = "secrets.toml"

default_log_format = "<bold>[{time:YYYY-MM-DD HH:mm}]</bold> <lvl>[{level}]</lvl> {message}"

default_app_info_importers = (ExodusImporter(), AppStoreImporter(), PlayStoreImporter())
default_device_importers = (IntuneImporter(),)
default_app_analyzers = (GPTAnalyzer(), PermissionsAnalyzer(), TrackerAnalyzer())
