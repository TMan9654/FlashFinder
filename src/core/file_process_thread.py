
from subprocess import check_output, CalledProcessError, STDOUT, CREATE_NO_WINDOW
from PySide6.QtCore import QThread, Signal

class FileProcessThread(QThread):
    finished_signal = Signal(str)

    def __init__(self, path, handle_path):
        super().__init__()
        self.path = path
        self.handle_path = handle_path

    def run(self):
        result = self.get_file_processes()
        self.finished_signal.emit(result)

    def get_file_processes(self):
        try:
            result = check_output([self.handle_path, "-nobanner", self.path], stderr=STDOUT, text=True, creationflags=CREATE_NO_WINDOW)
            lines = result.splitlines()
            filtered_lines = set([line.split(" type")[0] for line in lines])
            filtered_result = "\n".join(filtered_lines)
            
            return filtered_result
        except CalledProcessError as e:
            return str(e.output)

