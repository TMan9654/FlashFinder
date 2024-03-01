
from ...config.config import VERSION, DATA_PATH, COMPUTERNAME

from os import path
from PySide6.QtWidgets import QWidget, QGroupBox, QLabel, QTextEdit, QPushButton, QVBoxLayout, QFileDialog

class About(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        about_group = QGroupBox()
        self.developer_label = QLabel("Developer: Terrin Burns")
        self.version_label = QLabel(f"Version: {VERSION}")
        
        description_group = QGroupBox("Description")
        self.description_text = QLabel(
        """FlashFinder is a windows file explorer replacement that boasts some enhanced features.\n
Features such as fast and advanced searching, file comparison, power renaming, and tabbed browsing to name a few.\n
Take a look at the documentation to learn more.\n
Review the changelog to learn about new additions in each update."""
        )
        
        suggestion_group = QGroupBox("Suggestions / Report Bug:")
        self.suggestion_text = QTextEdit()
        self.suggestion_submit = QPushButton("Submit Suggestion / Bug")
        self.suggestion_submit.clicked.connect(self.submit_suggestion)
        self.attachment_path = None
        self.attach_button = QPushButton("Attach File")
        self.attach_button.clicked.connect(self.attach_file)
        
        main_layout = QVBoxLayout()
        about_group_layout = QVBoxLayout()
        description_group_layout = QVBoxLayout()
        suggestion_group_layout = QVBoxLayout()
        
        about_group_layout.addWidget(self.developer_label)
        about_group_layout.addWidget(self.version_label)
        description_group_layout.addWidget(self.description_text)
        suggestion_group_layout.addWidget(self.suggestion_text)
        suggestion_group_layout.addWidget(self.attach_button)
        suggestion_group_layout.addWidget(self.suggestion_submit)
        main_layout.addWidget(about_group)
        main_layout.addWidget(description_group)
        main_layout.addWidget(suggestion_group)
        
        about_group.setLayout(about_group_layout)
        description_group.setLayout(description_group_layout)
        suggestion_group.setLayout(suggestion_group_layout)
        self.setLayout(main_layout)
        
        self.setStyleSheet("""
            QLabel {
                color: black;
                background-color: #ffffff;
                font: 14px Arial, sans-serif;
            }
            QWidget {
                background-color: #f0f0f0;
            }
            QTextEdit {
                background-color: #ffffff;
                font: 13px Arial, sans-serif;
            }
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                padding: 3px 5px;
                text-align: center;
                text-decoration: none;
                font-size: 14px;
                margin: 4px 2px;
                border-radius: 4px;
            }
        """)

    def attach_file(self):
        self.attachment_path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*)")
        if self.attachment_path:
            self.attach_button.setText(f"Attached: {path.basename(self.attachment_path)}")
        
    def submit_suggestion(self):
        from datetime import datetime
        from shutil import copy
        suggestion = self.suggestion_text.toPlainText()
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
        formatted_suggestion = (
            f"========================================\n"
            f"System Name: {COMPUTERNAME}\n"
            f"Date & Time: {current_datetime}\n"
            f"Suggestion:\n{suggestion}\n"
        )
        
        with open(path.join(self.data_path, "User Suggestions.txt"), "a") as file:
            file.write(formatted_suggestion)
            if self.attachment_path:
                basename = path.basename(self.attachment_path)
                unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{basename}"
                destination_path = path.join(DATA_PATH, unique_filename)          
                copy(self.attachment_path, destination_path)                
                file.write(f"Attached file: {destination_path}\n")

            file.write("========================================\n\n")
        self.suggestion_text.clear()
        self.attachment_path = None
        self.attach_button.setText("Attach File")