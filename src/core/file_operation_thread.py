
from os import path, walk
from PySide6.QtCore import QThread, Signal

class FileOperationThread(QThread):
    import zipfile
    operationStarted = Signal(str)
    operationFinished = Signal(str)
    operationError = Signal(str)

    def __init__(self, operation, file_paths):
        super().__init__()
        self.operation = operation
        self.file_paths = file_paths

    def run(self):
        try:
            if self.operation == "compress":
                self.compress_items()
            elif self.operation == "extract":
                self.extract_item(self.file_paths[0])  # Assuming only one path is passed for extraction
            self.operationFinished.emit("Operation completed successfully!")
        except Exception as e:
            self.operationError.emit(str(e))

    def compress_items(self):
        zip_name = self.file_paths[0] + ".zip" if len(self.file_paths) == 1 else "compressed_items.zip"
        with self.zipfile.ZipFile(zip_name, "w", compression=self.zipfile.ZIP_DEFLATED) as zipf:
            for file_path in self.file_paths:
                if path.isdir(file_path):
                    for dirpath, dirnames, filenames in walk(file_path):
                        for filename in filenames:
                            relative_path = path.relpath(path.join(dirpath, filename), path)
                            zipf.write(path.join(dirpath, filename), arcname=relative_path)
                else:
                    zipf.write(path, arcname=path.basename(path))

    def extract_item(self, zip_path):
        extract_folder = path.splitext(zip_path)[0]
        with self.zipfile.ZipFile(zip_path, "r") as zipf:
            zipf.extractall(extract_folder)

