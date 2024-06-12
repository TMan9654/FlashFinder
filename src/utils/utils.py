from os import path

def fix_coordinate(value: int) -> int:
    """Fixes the coordinates when calculating for multi-monitor setups."""
    if value > 2**15:
        return value - 2**16
    return value

def save_settings(settings_type: str, settings: dict) -> None:
    from json import dump
    settings_path = _get_settings_path(settings_type)

    if settings_path:
        with open(settings_path, "w") as f:
            dump(settings, f, indent=4)


def load_settings(settings_type: str) -> dict:
    from json import load
    settings = None
    settings_path = _get_settings_path(settings_type)

    if settings_path and path.exists(settings_path):
        with open(settings_path, "r") as f:
            settings = load(f)
            if settings.keys() != _load_default_settings(settings_type).keys():
                default_settings = _load_default_settings(settings_type)
                for key in default_settings.keys():
                    if key not in settings.keys():
                        settings[key] = default_settings[key]
    if not settings:
        settings = _load_default_settings(settings_type)
    save_settings(settings_path, settings)
    return settings

def _load_default_settings(settings_type: str) -> dict:
    default_settings = None
    if settings_type == "compare":
        default_settings = {
                "PAGE_SIZES": {
                    "AUTO": (None, None),
                    "LETTER": (8.5, 11),
                    "ANSI A": (11, 8.5),
                    "ANSI B": (17, 11),
                    "ANSI C": (22, 17),
                    "ANSI D": (34, 22)
                },
                "DPI_LEVELS": [75, 150, 300, 600, 1200, 1800],
                "DPI_LABELS": [
                    "Low DPI: Draft Quality [75]",
                    "Low DPI: Viewing Only [150]",
                    "Medium DPI: Printable [300]",
                    "Standard DPI [600]",
                    "High DPI [1200]: Professional Quality",
                    "Max DPI [1800]: Large File Size"
                ],
                "INCLUDE_IMAGES": {"New Copy": False, "Old Copy": False, "Markup": True, "Difference": True, "Overlay": True},
                "DPI": "Medium DPI: Printable [300]",
                "DPI_LEVEL": 300,
                "PAGE_SIZE": "ANSI B",
                "THRESHOLD": 128,
                "MIN_AREA": 20,
                "EPSILON": 0.0,
                "OUTPUT_PATH": None,
                "SCALE_OUTPUT": True,
                "OUTPUT_BW": False,
                "OUTPUT_GS": False,
                "REDUCE_FILESIZE": True,
                "MAIN_PAGE": "New Document"
        }
    elif settings_type == "search":
        default_settings = {
            "INCLUDE_SUBFOLDERS": True,
            "EXCLUDE_PATHS": ["$Recycle.Bin", "$RECYCLE.BIN", "System Volume Information", "Windows", "Program Files", "Program Files (x86)",  "ProgramData", "Recovery", "AppData", "x86", "x64", "mysys64", "mysys32"],
            "INDEXED_SEARCH": True,
            "CACHED_SEARCH": True,
            "HISTORY_LIFETIME": 259200
        }
    elif settings_type == "general":
        default_settings = {
            "RELOAD_MAIN_TAB": False,
            "SCROLL_TO": False,
            "EXTERNAL_DROP_MODE": "Paste"
        }
    return default_settings

def _get_settings_path(settings_type: str) -> str:
    from ..config.config import SETTINGS_PATH, COMPUTERNAME
    settings_path = None
    if settings_type == "compare":
        settings_path = path.join(SETTINGS_PATH, f"{COMPUTERNAME}_compare-settings.json") 
    elif settings_type == "search":
        settings_path = path.join(SETTINGS_PATH, f"{COMPUTERNAME}_search-settings.json")
    elif settings_type == "general":
        settings_path = path.join(SETTINGS_PATH, f"{COMPUTERNAME}_general-settings.json")
    return settings_path

def check_config_paths() -> None:
    from os import mkdir
    from ..config.config import DATA_PATH, TEMP_PATH
    
    if not path.exists(DATA_PATH):
        mkdir(DATA_PATH)
    if not path.exists(TEMP_PATH):
        mkdir(TEMP_PATH)
