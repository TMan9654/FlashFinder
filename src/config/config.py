from os import path, environ, name
from darkdetect import isDark

VERSION = "7.5.4"

COMPUTERNAME = environ.get("COMPUTERNAME", "DefaultName")

BASE_PATH = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
DATA_PATH = path.join(BASE_PATH, "data")
DOCS_PATH = path.join(BASE_PATH, "docs")
ICONS_PATH = path.join(BASE_PATH, "icons")
INDEXES_PATH = path.join(BASE_PATH, "indexes")
SETTINGS_PATH = path.join(BASE_PATH, "settings")
TEMP_PATH = path.join(BASE_PATH, f"temp\\{COMPUTERNAME}")

IS_DARK = isDark()