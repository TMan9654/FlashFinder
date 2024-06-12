from ..config.config import INDEXES_PATH, COMPUTERNAME, SETTINGS_PATH
from ..utils.utils import load_settings

from time import sleep, time
from json import load, dump
from os import path, remove, walk, environ
from pickle import dump as pdump
from win32file import GetDriveType, DRIVE_REMOTE
from win32api import GetLogicalDriveStrings
from filelock import FileLock, Timeout
from datetime import datetime
from multiprocessing import Process

class FileIndexer(Process):
    def __init__(self):
        super(FileIndexer, self).__init__()
        self.rebuild_signal_path = path.join(INDEXES_PATH, "rebuild_signal")
        self.excluded_paths = self.load_exclude_paths()
        self.counter = 0
        self.local_lock = None
        self.num_rebuilt = 0
        self.previous_status = None
        
    def _claim_network_drive(self, drive: str) -> FileLock:
        """Acquires the network file index lock."""
        lock_file = path.join(INDEXES_PATH, f"Drive_{drive}_Claimed.lock")
        lock = FileLock(lock_file, timeout=0.5)
        try:
            lock.acquire()
            return lock
        except (Timeout, FileExistsError):
            return None
        
    def _release_network_drive(self, lock: FileLock):
        """Releases the network file index lock."""
        if lock:
            lock.release()

    def _claim_local_indexing(self) -> FileLock:
        """Acquires the local file indexing lock."""
        lock_file = path.join(INDEXES_PATH, f"{COMPUTERNAME}_Local_Indexing_Claimed.lock")
        lock = FileLock(lock_file, timeout=0.5)
        sleep(2)
        try:
            lock.acquire()
            return lock
        except (Timeout, FileExistsError):
            return None

    def _release_local_indexing(self, lock: FileLock):
        """Releases the local file indexing lock."""
        if lock:
            lock.release()

    def run(self):
        """Runs a continuous loop for maintaining index files and communicating with the parent process."""
        self.local_lock = self._claim_local_indexing()
        network_lock = None
        try:
            while True:
                active_drives = self._get_active_drives()
                for drive in active_drives:
                    if self._is_network_drive(drive):
                        network_lock = self._claim_network_drive(drive)
                        if network_lock and self._check_index(drive, len(active_drives)):
                            self._update_status(f"Indexing {drive} drive...")
                            self._index_drive(drive)
                        self._release_network_drive(network_lock)
                    elif self.local_lock:
                        if self._check_index(drive, len(active_drives)):
                            self._update_status(f"Indexing {drive} drive...")
                            self._index_drive(drive)
                    self._update_status("Idle")
                    sleep(5)
        finally:
            self._release_local_indexing(self.local_lock)
            self._remove_indexer_running_file()
            self._release_network_drive(network_lock)
                
    def _remove_indexer_running_file(self):
        "Removes the indexers signal file for cleanup."
        if path.exists(path.join(INDEXES_PATH, f"{COMPUTERNAME}_indexer_running")):
            try:
                remove(path.join(INDEXES_PATH, f"{COMPUTERNAME}_indexer_running"))
            except PermissionError:
                sleep(1)
                self._remove_indexer_running_file()
                
    def _is_network_drive(self, drive: str) -> bool:
        """Returns a boolean value indicating whether the drive path is a network drive."""
        drive_type = GetDriveType(f"{drive}:\\")
        return drive_type == DRIVE_REMOTE

    def _get_active_drives(self) -> list:
        """Returns a list of active drives."""
        drives = GetLogicalDriveStrings()
        drives = drives.split("\000")[:-1]
        return [drive[0] for drive in drives]

    def _check_index(self, drive: str, num_active_drives: int) -> bool:
        """Checks if the index file requires reindexing based on the rebuild button being pressed or the path exceeds the dynamic indexing time."""
        if path.exists(path.join(SETTINGS_PATH, f"{COMPUTERNAME}_rebuild")) and self.num_rebuilt != num_active_drives:
            self.num_rebuilt += 1
            return True
        else:
            self._rebuilt()
            self.num_rebuilt = 0
        index_path = self._get_index_path(drive)
        last_indexed_time = 0
        if path.exists(index_path):
            last_indexed_time = path.getmtime(index_path)

        previous_duration = self._get_previous_duration(drive)
        reindex_interval = min(max(3600, previous_duration * 12), 3600*12)

        if not path.exists(index_path) or time() - last_indexed_time >= reindex_interval:
            return True
        return False
    
    def _rebuilt(self) -> None:
        """Removes the rebuild signal file indicating all indexes have been rebuilt."""
        if path.exists(path.join(SETTINGS_PATH, f"{COMPUTERNAME}_rebuild")):
            remove(path.join(SETTINGS_PATH, f"{COMPUTERNAME}_rebuild"))
    
    def _get_previous_duration(self, drive: str) -> int:
        """Returns the previous duration taken to index the given drive."""
        duration_path = self._get_duration_path(drive)
        if path.exists(duration_path):
            with open(duration_path, 'r') as f:
                index_time = f.read().strip()
                if index_time:
                    return int(index_time)
        return 3600

    def _get_duration_path(self, drive: str) -> str:
        """Returns the file path for the duration file for the given drive."""
        return path.join(INDEXES_PATH, f"{COMPUTERNAME}_Drive_{drive}_Duration")

    def _index_drive(self, drive: str):
        """Indexes the given drive outputting a indexing duration file and a pickle index."""
        start_time = time()
        drive_path = f"{drive}:\\"
        index_path = self._get_index_path(drive)
        indexed_files = {}
        
        self._update_status(f"Indexing {drive_path}...")
        for root, dirs, files in walk(drive_path):
            dirs[:] = [d for d in dirs if d not in self.excluded_paths]
            for name in files + dirs:
                full_path = path.join(root, name)
                if path.isdir(full_path):
                    file_type, file_ext = "File Folder", None
                else:
                    name, file_ext = path.splitext(name)
                    file_type = file_ext + " File"
                if path.exists(full_path):
                    try:
                        creation_date = datetime.fromtimestamp(path.getctime(full_path)).strftime("%d/%m/%Y %I:%M %p")
                    except:
                        creation_date = "ERROR"
                    try:
                        modification_date = datetime.fromtimestamp(path.getmtime(full_path)).strftime("%d/%m/%Y %I:%M %p")
                    except:
                        modification_date = "ERROR"                    
                    indexed_files[full_path] = (
                        name + file_ext if file_ext else name, 
                        name.lower() + file_ext.lower() if file_ext else name.lower(), 
                        file_type, file_ext.lower() if file_ext else file_ext, 
                        creation_date, 
                        modification_date
                    )
        metadata = {
            "TOTAL_INDEXED": len(indexed_files)
        }
        with open(index_path, "wb") as pklfile:
            pdump({"index": indexed_files, "metadata": metadata}, pklfile, protocol=5)
                         
        with open(self._get_duration_path(drive), 'w') as f:
            f.write(str(int(time() - start_time)))

        self._update_status("Idle")
    
    def _get_index_path(self, drive: str) -> str:
        """Returns the index path for the given drive."""
        index_path = path.join(INDEXES_PATH, f"{COMPUTERNAME}_Drive_{drive}_Index.pkl")
        if self._is_network_drive(drive):
            index_path = path.join(INDEXES_PATH, f"Drive_{drive}_Index.pkl")
        return index_path

    def _update_status(self, status: str):
        """Writes the indexer status to the indexers signal file for communication with the parent process."""
        status_file = path.join(INDEXES_PATH, f"{COMPUTERNAME}_indexer_running")
        if status != self.previous_status:
            self.previous_status = status
            try:
                with open(status_file, "w") as f:
                    f.write(status)
            except PermissionError:
                self._update_status(status)
                
    def load_exclude_paths(self) -> list:
        """Returns a list paths for the indexer to exclude from indexing. Loaded from the settings file."""
        search_settings = load_settings("search")
        if "EXCLUDE_PATHS" in search_settings:
            excluded_paths = search_settings["EXCLUDE_PATHS"]
        return excluded_paths
