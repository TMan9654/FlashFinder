
from os import path
from re import error, sub
from PySide6.QtCore import QThread, Signal

class RenameWorker(QThread):
    preview_updated = Signal(list)

    def __init__(self, file_paths: list, settings: dict):
        super(RenameWorker, self).__init__()
        self.file_paths = file_paths
        self.settings = settings
        self.enumeration_counter = 0

    def run(self):
        preview_data = []
        for file_path in self.file_paths:
            new_name = self.generate_new_name(path.basename(file_path), self.settings)
            preview_data.append((path.basename(file_path), new_name))
        self.preview_updated.emit(preview_data)

    def generate_new_name(self, name: str, settings: dict) -> str:
        # Apply search & replace
        if settings["use_regex"]:
            try:
                if settings["match_all"]:
                    name = sub(settings["search"], settings["replace"], name)
                else:
                    # Replace only the first occurrence
                    name = sub(settings["search"], settings["replace"], name, count=1)
            except error:
                pass
        else:
            if settings["match_all"]:
                name = name.replace(settings["search"], settings["replace"])
            else:
                # Replace only the first occurrence
                name = name.replace(settings["search"], settings["replace"], 1)
        # Apply text formatting
        if settings["formatting"] == "lowercase":
            name = name.lower()
        elif settings["formatting"] == "uppercase":
            name = name.upper()
        elif settings["formatting"] == "titlecase":
            name = name.title()
        elif settings["formatting"] == "capitalize":
            words = name.split()
            name = " ".join(word.capitalize() for word in words)

        # Enumerate items
        if settings["enumerate"]:
            name_without_extension, extension = path.splitext(name)
            self.enumeration_counter += 1
            name = f"{name_without_extension}_{self.enumeration_counter}{extension}"
        return name
    
    def reset_counter(self):
        self.enumeration_counter = 0

