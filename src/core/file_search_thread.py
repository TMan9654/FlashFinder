
from ..config.config import COMPUTERNAME, INDEXES_PATH, SETTINGS_PATH

from re import compile, search, IGNORECASE
from time import time, ctime
from os import path, listdir, walk
from pickle import load as pload
from json import load as jload
from win32api import GetLogicalDriveStrings
from PySide6.QtCore import QThread, Signal


class FileSearchThread(QThread):
    searchFinished = Signal(int, float)
    noMatchingFiles = Signal()
    foundMatchingFile = Signal(dict)
    progressUpdated = Signal(int)

    def __init__(self, search_text: str, current_address: str, index_count: int, index_cache: dict, mode: int = 0):
        super().__init__()
        search_settings = self.load_settings()
        self.INDEXED_SEARCH = search_settings.get("INDEXED_SEARCH")
        self.INCLUDE_SUBFOLDERS = search_settings.get("INCLUDE_SUBFOLDERS")
        self.SEARCH_PATTERN = False
        self.search_text = search_text.lower()
        self.current_address = current_address
        self.mode = mode
        self.results_count = 0
        self.index_count = index_count
        self.index_cache = index_cache
        self.command_pattern = compile(r"(!?\w+)(?::(\w+))?\(([^)]+)\)")
        self.exit_flag = False

    def run(self) -> None:
        start_time = time()
        if self.search_text:
            if self.search_text.startswith("::"):
                self.SEARCH_PATTERN = compile(self.search_text.replace("::", ""), IGNORECASE)
            
            if self.INDEXED_SEARCH:
                if self.index_cache:
                    if self.search_cache():
                        self.noMatchingFiles.emit()
                else:
                    if self.search_indexed():
                        self.noMatchingFiles.emit()
            else:
                if self.search_walk():
                    self.noMatchingFiles.emit()
        end_time = time()
        search_time = end_time - start_time
        self.searchFinished.emit(self.results_count, search_time)
        return

    def stop(self) -> None:
        self.exit_flag = True

    def check_commands(self, commands: str, name: str, file_type: str, index_path: str) -> bool:
        for command, mode, args in commands:
            mode = mode or "all"
    
            args_list = [arg.strip().lower() for arg in args.split(",")]
            
            if self.INCLUDE_SUBFOLDERS:
                contains_checks = [arg in name and self.current_address in index_path for arg in args_list]
                equals_checks = [arg == name and self.current_address in index_path for arg in args_list]
                type_checks = [(arg == file_type if "." not in file_type else arg == file_type.split(".")[-1]) and self.current_address in index_path if file_type else arg == "folder" for arg in args_list]
            else:
                contains_checks = [arg in name for arg in args_list]
                equals_checks = [arg == name for arg in args_list]
                type_checks = [(arg == file_type if "." not in file_type else arg == file_type.split(".")[-1]) if file_type else arg == "folder" for arg in args_list]
    
            if command == "contains":
                if (mode == "all" and not all(contains_checks)) or \
                   (mode == "any" and not any(contains_checks)):
                    return False
    
            elif command == "!contain":
                if any(contains_checks):
                    return False
    
            elif command == "equals":
                if (mode == "all" and not all(equals_checks)) or \
                   (mode == "any" and not any(equals_checks)):
                    return False
    
            elif command == "!equal":
                if any(equals_checks):
                    return False
    
            elif command == "type":
                if (mode == "all" and not all(type_checks)) or \
                   (mode == "any" and not any(type_checks)):
                    return False
    
            elif command == "!type":
                if all(type_checks):
                    return False
        return True

    def check_search_text(self, search_text: str, name: str, index_path: str) -> bool:
        if self.SEARCH_PATTERN:
            is_match = bool(search(self.SEARCH_PATTERN, name)) 
        else:
            is_match = search_text in name
            
        if self.mode != 0 and self.INCLUDE_SUBFOLDERS and is_match:
            return self.current_address in index_path
        
        return is_match

    def update_progress(self, processed_files: int, total_files: int, last_emitted_progress: int) -> int:
        if processed_files > 0 and total_files > 0:
            progress_percent = processed_files * 90 // total_files     
            self.progressUpdated.emit(progress_percent)
            return progress_percent
        
        return last_emitted_progress

    def search_cache(self) -> bool:
        if self.mode != 0 and not self.INCLUDE_SUBFOLDERS:
            matches = self.search_current_path(self.command_pattern.findall(self.search_text))
            if matches:
                self.foundMatchingFile.emit(matches)
                return False
            return True
        
        pickle_files = self.index_cache.keys()
    
        processed_files = 0
        last_emitted_progress = 0
        commands = self.command_pattern.findall(self.search_text)

        no_result = True
        matches = {}
        for pklfile in pickle_files:
            file_index = self.index_cache[pklfile]
            for index_path, (name, name_lower, file_type, file_type_lower, creation_date, modification_date) in file_index.items():
                
                if self.exit_flag:
                    return False
                
                is_match = self.check_commands(commands, name_lower, file_type_lower, index_path) if commands else self.check_search_text(self.search_text, name_lower, index_path)
                
                if is_match:
                    no_result = False
                    matches[index_path] = (name, file_type, creation_date, modification_date)

                processed_files += 1
                if processed_files % 10000 == 0:
                    last_emitted_progress = self.update_progress(processed_files, self.index_count, last_emitted_progress)
    
        self.results_count = len(matches)
        self.foundMatchingFile.emit(matches)
        return no_result

    def search_indexed(self) -> bool:
        if self.mode != 0 and not self.INCLUDE_SUBFOLDERS:
            matches = self.search_current_path(self.command_pattern.findall(self.search_text))
            if matches:
                self.foundMatchingFile.emit(matches)
                return False
            return True
       
        mounted_drives = self.get_mounted_drives()
        pickle_files = [
            path.join(INDEXES_PATH, file)
            for file in listdir(INDEXES_PATH)
            if file.endswith(".pkl") and (file.startswith("Drive") or file.startswith(COMPUTERNAME)) and file.split("_")[-2] in mounted_drives
        ]
        pickle_files.sort()
    
        processed_files = 0
        last_emitted_progress = 0
        commands = self.command_pattern.findall(self.search_text)

        no_result = True
        matches = {}
        for pklfile in pickle_files:
            with open(pklfile, "rb") as f:
                file_index = pload(f)["index"]
                for index_path, (name, name_lower, file_type, file_ext, creation_date, modification_date) in file_index.items():
                    if self.exit_flag:
                        self.foundMatchingFile.emit(matches)
                        return no_result
                    
                    is_match = self.check_commands(commands, name_lower, file_ext, index_path) if commands else self.check_search_text(self.search_text, name_lower, index_path)
                        
                    if is_match:
                        no_result = False
                        matches[index_path] = (name, file_type, creation_date, modification_date)
    
                    processed_files += 1
                    if processed_files % 10000 == 0:
                        last_emitted_progress = self.update_progress(processed_files, self.index_count, last_emitted_progress)
    
        self.results_count = len(matches)
        self.foundMatchingFile.emit(matches)
        return no_result

    def search_walk(self) -> bool:
        if self.mode != 0 and not self.INCLUDE_SUBFOLDERS:
            matches = self.search_current_path(self.command_pattern.findall(self.search_text))
            if matches:
                self.foundMatchingFile.emit(matches)
                return False
            return True
        
        search_directories = self.get_mounted_drives()
        processed_files = 0
        last_emitted_progress = 0
        commands = self.command_pattern.findall(self.search_text)

        no_result = True
        matches = {}
        total_files = self.get_total_files(search_directories)
        for directory in search_directories:
            directory = directory + ":\\"
            for foldername, subfolders, filenames in walk(directory):
                for name, is_file in [(f, True) for f in filenames] + [(s, False) for s in subfolders]:
                    index_path = path.join(foldername, name)
                    file_type = "Folder" if not is_file else path.splitext(name)[1].upper()[1:]

                    if self.exit_flag:
                        return False

                    name_lower = name.lower()
                    file_type_lower = file_type.lower()

                    is_match = self.check_commands(commands, name_lower, file_type_lower, index_path) if commands else self.check_search_text(self.search_text, name_lower, index_path)
                    
                    if is_match:
                        no_result = False
                        creation_date = ctime(path.getctime(index_path))
                        modification_date = ctime(path.getmtime(index_path))
                        matches[index_path] = (name, file_type, creation_date, modification_date)

                    processed_files += 1
                    if processed_files % 10000 == 0:
                        last_emitted_progress = self.update_progress(processed_files, total_files, last_emitted_progress)

        self.results_count = len(matches)
        self.foundMatchingFile.emit(matches)
        return no_result

    def search_current_path(self, commands: list) -> dict:
        matches = {}
        processed_files = 0
        last_emitted_progress = 0
        items = listdir(self.current_address)
        for item in items:
            index_path = path.join(self.current_address, item)
            name, name_lower, file_type, file_type_lower, creation_date, modification_date = self.process_item(item, index_path)
            is_match = self.check_commands(commands, name_lower+file_type_lower, file_type_lower, index_path) if commands else self.check_search_text(self.search_text, name_lower+file_type_lower, index_path)
            if is_match:
                matches[index_path] = (name + file_type, file_type, creation_date, modification_date)
            processed_files += 1
            last_emitted_progress = self.update_progress(processed_files, len(items), last_emitted_progress)      
        self.results_count = len(matches)
        return matches

    def process_item(self, item: str, index_path: str) -> tuple:
        name, file_type = path.splitext(item)
        name_lower = name.lower()
        file_type_lower = file_type.lower()
        try:
            creation_date = ctime(path.getctime(index_path))
            modification_date = ctime(path.getmtime(index_path))
        except OSError:
            creation_date = "ERROR"
            modification_date = "ERROR"
        
        return (name + file_type, name_lower + file_type_lower, file_type, file_type_lower, creation_date, modification_date)

    def get_total_files(self, directories):
        total = 0
        for directory in directories:
            for _, subfolders, filenames in walk(directory + ":\\"):
                total += len(filenames) + len(subfolders)
        return total

    def get_mounted_drives(self) -> list:
        drives = GetLogicalDriveStrings()
        drives = drives.split("\000")[:-1]
        return [drive[0] for drive in drives]

    def load_settings(self):
        if path.exists(path.join(SETTINGS_PATH, f"{COMPUTERNAME}_search-settings.json")):
            with open(path.join(SETTINGS_PATH, f"{COMPUTERNAME}_search-settings.json"), "r") as f:
                search_settings = jload(f)
        else:
            search_settings = {
                "INCLUDE_SUBFOLDERS": True,
                "INDEXED_SEARCH": True
            }
        return search_settings

