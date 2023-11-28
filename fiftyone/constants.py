"""
Package-wide constants.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
from datetime import datetime
import os

from packaging.version import Version

try:
    from importlib.metadata import metadata  # Python 3.8
except ImportError:
    from importlib_metadata import metadata  # Python < 3.8


CLIENT_TYPE = "fiftyone"

FIFTYONE_DIR = os.path.dirname(os.path.abspath(__file__))
FIFTYONE_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".fiftyone")
FIFTYONE_CONFIG_PATH = os.path.join(FIFTYONE_CONFIG_DIR, "config.json")
FIFTYONE_ANNOTATION_CONFIG_PATH = os.path.join(
    FIFTYONE_CONFIG_DIR, "annotation_config.json"
)
FIFTYONE_EVALUATION_CONFIG_PATH = os.path.join(
    FIFTYONE_CONFIG_DIR, "evaluation_config.json"
)
FIFTYONE_APP_CONFIG_PATH = os.path.join(FIFTYONE_CONFIG_DIR, "app_config.json")
BASE_DIR = os.path.dirname(FIFTYONE_DIR)
TEAMS_PATH = os.path.join(FIFTYONE_CONFIG_DIR, "var", "teams.json")
WELCOME_PATH = os.path.join(FIFTYONE_CONFIG_DIR, "var", "welcome.json")
RESOURCES_DIR = os.path.join(FIFTYONE_DIR, "resources")

#
# The compatible versions for this client
#
# RULES: Datasets from all compatible versions must be...
#   - Loadable by this client without error
#   - Editable by this client without causing any database edits that would
#     break the original client's ability to work with the dataset
#
# This setting may be ``None`` if this client has no compatibility with other
# versions
#
COMPATIBLE_VERSIONS = ">=0.19,<0.24"

# Package metadata
_META = metadata("fiftyone")
NAME = _META["name"]
VERSION = _META["version"]
DESCRIPTION = _META["summary"]
AUTHOR = _META["author"]
AUTHOR_EMAIL = _META["author-email"]
URL = _META["home-page"]
LICENSE = _META["license"]
VERSION_LONG = "FiftyOne v%s, %s" % (VERSION, AUTHOR)
COPYRIGHT = "2017-%d, %s" % (datetime.now().year, AUTHOR)

DEV_INSTALL = os.path.isdir(
    os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".git")
    )
)
RC_INSTALL = "rc" in VERSION

# App configuration
DEFAULT_APP_COLOR_POOL = [
    "#E69F00",  # orange
    "#56b4e9",  # skyblue
    "#009e74",  # bluegreen
    "#f0e442",  # yellow
    "#0072b2",  # blue
    "#d55e00",  # vermillion
    "#cc79a7",  # reddish purple
]

DEFAULT_COLOR_SCHEME = {
    "color_pool": DEFAULT_APP_COLOR_POOL,
    "fields": [],
    "label_tags": {"fieldColor": None, "valueColors": []},
    "default_mask_targets": [],
}

# MongoDB setup
try:
    from fiftyone.db import FIFTYONE_DB_BIN_DIR
except ImportError:
    # development installation
    FIFTYONE_DB_BIN_DIR = os.path.join(FIFTYONE_CONFIG_DIR, "bin")

DEFAULT_DB_DIR = os.path.join(FIFTYONE_CONFIG_DIR, "var", "lib", "mongo")
MIGRATIONS_PATH = os.path.join(FIFTYONE_CONFIG_DIR, "migrations")
MIGRATIONS_HEAD_PATH = os.path.join(MIGRATIONS_PATH, "head.json")
MIGRATIONS_REVISIONS_DIR = os.path.join(
    FIFTYONE_DIR, "migrations", "revisions"
)

MIN_MONGODB_VERSION = Version("4.4")
DATABASE_APPNAME = "fiftyone"

# Server setup
SERVER_DIR = os.path.join(FIFTYONE_DIR, "server")

# App setup
try:
    from fiftyone.desktop import FIFTYONE_DESKTOP_APP_DIR
except ImportError:
    FIFTYONE_DESKTOP_APP_DIR = os.path.normpath(
        os.path.join(FIFTYONE_DIR, "../app")
    )
