from ..config.config import BASE_PATH

from os import path, walk
from subprocess import check_output, CalledProcessError, STDOUT, CREATE_NO_WINDOW
from zipfile import ZipFile, ZIP_DEFLATED
from PySide6.QtCore import QThread, Signal


class FileOperationThread(QThread):  
    operationStarted = Signal(str)
    operationFinished = Signal(set)
    operationError = Signal(str)

    def __init__(self, operation: str, file_paths: list, destination: str=None):
        super().__init__()
        self.operation = operation
        self.file_paths = file_paths
        if destination:
            self.destination = destination

    def run(self):
        try:
            if self.operation == "compress":
                self.compress_items()
                self.operationFinished.emit(("compress", "Operation completed successfully!"))
            elif self.operation == "extract":
                self.extract_items()
                self.operationFinished.emit(("extract", "Operation completed successfully!"))
            elif self.operation == "processes":
                result = self.get_file_processes()
                self.operationFinished.emit(("processes", result))
        except Exception as e:
            self.operationError.emit(str(e))

    def compress_items(self):
        zip_name = self.file_paths[0] + ".zip" if len(self.file_paths) == 1 else "compressed_items.zip"
        with ZipFile(zip_name, 'w', compression=ZIP_DEFLATED) as zipf:
            for file_path in self.file_paths:
                if path.isdir(file_path):
                    for dirpath, dirnames, filenames in walk(file_path):
                        for filename in filenames:
                            file_to_zip = path.join(dirpath, filename)
                            relative_path = path.relpath(file_to_zip, start=path.dirname(file_path))
                            zipf.write(file_to_zip, arcname=relative_path)
                else:
                    zipf.write(file_path, arcname=path.basename(file_path))

    def extract_items(self):
        for zip_path in self.file_paths:
            extract_folder = path.splitext(zip_path)[0]
            with ZipFile(zip_path, "r") as zipf:
                zipf.extractall(extract_folder)

    def get_file_processes(self):
        try:
            result = check_output([path.join(BASE_PATH, "handle.exe"), "-nobanner", self.file_paths[0]], stderr=STDOUT, text=True, creationflags=CREATE_NO_WINDOW)
            lines = result.splitlines()
            filtered_lines = set([line.split(" type")[0] for line in lines])
            filtered_result = "\n".join(filtered_lines)
            
            return filtered_result
        except CalledProcessError as e:
            return str(e.output)

