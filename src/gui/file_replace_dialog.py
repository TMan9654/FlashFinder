
from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton

class FileReplaceDialog(QDialog):
    Replace, ReplaceAll, Rename, Cancel = range(4)

    def __init__(self, parent, filename: str, num_files: int):
        super().__init__(parent)
        self.setWindowTitle("File Exists")
        layout = QVBoxLayout(self)
        
        label = QLabel(f"The file '{filename}' already exists. What would you like to do?")
        layout.addWidget(label)

        replace_button = QPushButton("Replace")
        replace_all_button = QPushButton("Replace All")
        rename_button = QPushButton("Rename")
        cancel_button = QPushButton("Cancel")

        replace_button.clicked.connect(lambda: self.done(self.Replace))
        replace_all_button.clicked.connect(lambda: self.done(self.ReplaceAll))
        rename_button.clicked.connect(lambda: self.done(self.Rename))
        cancel_button.clicked.connect(lambda: self.done(self.Cancel))

        layout.addWidget(replace_button)
        if num_files > 1:
            layout.addWidget(replace_all_button)
        layout.addWidget(rename_button)
        layout.addWidget(cancel_button)
        
    def closeEvent(self, event: QEvent):
        self.done(self.Cancel)

