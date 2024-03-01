from os import path, environ, name
from darkdetect import isDark

VERSION = "7.5.4"

COMPUTERNAME = environ.get("COMPUTERNAME", "DefaultName")

_desktop_path = path.join(environ["USERPROFILE"], "Desktop")
_onedrive_desktop_path = path.join(environ["USERPROFILE"], "OneDrive", "Desktop")
DESKTOP_PATH = _desktop_path if path.exists(_desktop_path) else _onedrive_desktop_path
_documents_path = path.join(environ["USERPROFILE"], "Documents")
_onedrive_documents_path = path.join(environ["USERPROFILE"], "OneDrive", "Documents")
DOCUMENTS_PATH = _documents_path if path.exists(_documents_path) else _onedrive_documents_path
_pictures_path = path.join(environ["USERPROFILE"], "Pictures")
_onedrive_pictures_path = path.join(environ["USERPROFILE"], "OneDrive", "Pictures")
PICTURES_PATH = _pictures_path if path.exists(_pictures_path) else _onedrive_pictures_path


BASE_PATH = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
DATA_PATH = path.join(BASE_PATH, "data")
DOCS_PATH = path.join(BASE_PATH, "docs")
ICONS_PATH = path.join(BASE_PATH, "icons")
INDEXES_PATH = path.join(BASE_PATH, "indexes")
SETTINGS_PATH = path.join(BASE_PATH, "settings")
TEMP_PATH = path.join(BASE_PATH, f"temp\\{COMPUTERNAME}")

IS_DARK = isDark()