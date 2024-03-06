
from ..config.config import BASE_PATH, INDEXES_PATH, SETTINGS_PATH, COMPUTERNAME

from os import path, listdir
from subprocess import Popen
from pickle import load as pload
from json import load as jload
from json import dump
from PySide6.QtCore import QThread, Signal

class StatusCheckThread(QThread):
    import time
    
    statusChanged = Signal(str, int, dict)
    requestClose = Signal()
    
    def __init__(self, parent=None):
        super(StatusCheckThread, self).__init__(parent)
        self.search_settings_path = path.join(SETTINGS_PATH, f"{COMPUTERNAME}_search-settings.json")
        self.indexer_running_file = path.join(INDEXES_PATH, f"{COMPUTERNAME}_indexer_running")
        self.index_cache = {}
        self.previous_time = 0

    def run(self):
        last_status = "Idle"
        while True:
            self.check_for_update()
            if path.exists(self.indexer_running_file):
                with open(self.indexer_running_file, "r") as f:
                    status = f.read()
                    if status != last_status:
                        index_count = self.get_index_count()
                        if index_count >= 0:
                            self.statusChanged.emit(status, index_count, self.index_cache)
                            last_status = status
                        else:
                            self.statusChanged.emit("Indexer Error", index_count, self.index_cache)
            else:
                if last_status != "Idle":
                    index_count = self.get_index_count()
                    self.statusChanged.emit("Idle", index_count, self.index_cache)
                    last_status = "Idle"
            QThread.sleep(3)
            
    def check_for_update(self):
        if not path.exists(path.join(INDEXES_PATH, f"{COMPUTERNAME}_is_alive")):
            signal_file = open(path.join(INDEXES_PATH, f"{COMPUTERNAME}_is_alive"), "w")
            signal_file.close()
        for file in listdir(BASE_PATH):
            if "update-" in file.lower():
                Popen([f"{BASE_PATH}\\dialog.exe"])
                self.requestClose.emit()
            
    def get_index_count(self) -> int:
        if path.exists(self.indexer_running_file):
            with open(self.indexer_running_file, "r") as f:
                last_status = f.read()
        else:
            return -1
        search_settings = self.load_settings()
        indexed_count = 0
        for drive_letter in self.get_mounted_drives():
            hostname_file = path.join(INDEXES_PATH, f"{COMPUTERNAME}_Drive_{drive_letter}_Index.pkl")
            generic_file = path.join(INDEXES_PATH, f"Drive_{drive_letter}_Index.pkl")
            
            target_file = hostname_file if path.exists(hostname_file) else generic_file if path.exists(generic_file) else None
            
            if target_file:
                try:
                    with open(target_file, "rb") as pklfile:
                        data = pload(pklfile)
                        current_time = self.time.time()
                        if search_settings.get("CACHED_SEARCH"):
                            if not target_file in self.index_cache.keys() or current_time - self.previous_time >= 300:
                                self.previous_time = current_time
                                self.index_cache[target_file] = data["index"]
                                with open(self.indexer_running_file, "w") as f:
                                    f.write(last_status)
                        else:
                            if self.index_cache:
                                self.index_cache.clear()
                                with open(self.indexer_running_file, "w") as f:
                                    f.write(last_status)
                        indexed_count += data["metadata"]["TOTAL_INDEXED"]
                except PermissionError:
                    pass
        return indexed_count
    
    def get_mounted_drives(self) -> list:
        import win32api
        drives = win32api.GetLogicalDriveStrings()
        drives = drives.split("\000")[:-1]
        return [drive[0] for drive in drives]

    def load_settings(self) -> dict:
        default_settings = {
            "INCLUDE_SUBFOLDERS": False,
            "INDEXED_SEARCH": True,
            "CACHED_SEARCH": True
        }

        if path.exists(self.search_settings_path):
            with open(self.search_settings_path, "r") as f:
                search_settings = jload(f)
            updated = False
            for key, value in default_settings.items():
                if key not in search_settings:
                    search_settings[key] = value
                    updated = True

            if updated:
                with open(self.search_settings_path, "w") as f:
                    dump(search_settings, f, indent=4)
        else:
            search_settings = default_settings
            with open(self.search_settings_path, "w") as f:
                dump(search_settings, f, indent=4)

        return search_settings

