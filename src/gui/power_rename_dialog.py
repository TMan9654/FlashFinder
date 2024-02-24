
from ..core.rename_worker_thread import RenameWorker

from os import path, listdir
from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QCheckBox, QComboBox, QPushButton, QRadioButton, \
    QButtonGroup, QHBoxLayout, QListWidget

class PowerRenameDialog(QDialog):
    def __init__(self, paths: list, parent=None):
        super(PowerRenameDialog, self).__init__(parent)
        self.original_paths = paths.copy()
        self.paths = paths
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Power Rename")
        layout = QVBoxLayout()

        # Search and Replace
        self.search_label = QLabel("Search for:")
        self.search_edit = QLineEdit(self)
        layout.addWidget(self.search_label)
        layout.addWidget(self.search_edit)

        self.replace_label = QLabel("Replace with:")
        self.replace_edit = QLineEdit(self)
        layout.addWidget(self.replace_label)
        layout.addWidget(self.replace_edit)

        # Checkboxes
        self.include_all_checkbox = QCheckBox("Include All Items In Current Directory", self)
        self.regex_checkbox = QCheckBox("Use Regular Expressions", self)
        self.match_all_checkbox = QCheckBox("Match All Occurrences", self)
        self.case_sensitive_checkbox = QCheckBox("Case Sensitive", self)
        
        layout.addWidget(self.include_all_checkbox)
        layout.addWidget(self.regex_checkbox)
        layout.addWidget(self.match_all_checkbox)
        layout.addWidget(self.case_sensitive_checkbox)

        # Apply to options
        self.apply_to_label = QLabel("Apply to:")
        self.apply_to_combo = QComboBox()
        self.apply_to_combo.addItems(["Files", "Folders", "Both"])
        layout.addWidget(self.apply_to_label)
        layout.addWidget(self.apply_to_combo)

        # Include Subfolders and Enumerate items
        self.include_subfolders_button = QPushButton("Include Subfolders", self)
        self.include_subfolders_button.setCheckable(True)
        self.enumerate_items_button = QPushButton("Enumerate Selected Items", self)
        self.enumerate_items_button.setCheckable(True)
        layout.addWidget(self.include_subfolders_button)
        layout.addWidget(self.enumerate_items_button)

        # Text formatting options
        self.formatting_label = QLabel("Text Formatting:")
        self.lowercase_button = QRadioButton("All Lowercase")
        self.uppercase_button = QRadioButton("All Uppercase")
        self.titlecase_button = QRadioButton("Title Case")
        self.capitalize_button = QRadioButton("Capitalize Each Word")

        formatting_group = QButtonGroup(self)
        formatting_group.addButton(self.lowercase_button)
        formatting_group.addButton(self.uppercase_button)
        formatting_group.addButton(self.titlecase_button)
        formatting_group.addButton(self.capitalize_button)

        formatting_layout = QHBoxLayout()
        formatting_layout.addWidget(self.lowercase_button)
        formatting_layout.addWidget(self.uppercase_button)
        formatting_layout.addWidget(self.titlecase_button)
        formatting_layout.addWidget(self.capitalize_button)

        layout.addWidget(self.formatting_label)
        layout.addLayout(formatting_layout)

        # Preview section
        self.preview_list = QListWidget(self)
        layout.addWidget(QLabel("Preview:"))
        layout.addWidget(self.preview_list)

        # OK and Cancel buttons
        self.button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)
        self.button_layout.addWidget(self.ok_button)
        self.button_layout.addWidget(self.cancel_button)

        layout.addLayout(self.button_layout)

        self.setLayout(layout)
        
        self.rename_worker = None

        self.include_all_checkbox.stateChanged.connect(self.update_preview)
        self.search_edit.textChanged.connect(self.update_preview)
        self.replace_edit.textChanged.connect(self.update_preview)
        self.regex_checkbox.stateChanged.connect(self.update_preview)
        self.match_all_checkbox.stateChanged.connect(self.update_preview)
        self.case_sensitive_checkbox.stateChanged.connect(self.update_preview)
        self.apply_to_combo.currentIndexChanged.connect(self.update_preview)
        self.include_subfolders_button.toggled.connect(self.update_preview)
        self.enumerate_items_button.toggled.connect(self.update_preview)
        self.lowercase_button.toggled.connect(self.update_preview)
        self.uppercase_button.toggled.connect(self.update_preview)
        self.titlecase_button.toggled.connect(self.update_preview)
        self.capitalize_button.toggled.connect(self.update_preview)
        
        self.setStyleSheet("""
            QLabel {
                color: black;
                font: 14px Arial, sans-serif;
            }
            QSpinBox {
                color: black;
                font: 14px Arial, sans-serif;
                border: 1px solid #ccc;
                padding: 5px;
                background-color: #f0f0f0;
            }
            QComboBox { 
                background-color: #FFFFFF; 
                color: #333; 
                font: 14px Arial, sans-serif;
                border: 1px solid #CCC; 
            }
            QComboBox:hover { 
                background-color: #EDEDED; 
            }
            QComboBox:focus { 
                background-color: #E5E5E5; 
            }
            QComboBox:disabled { 
                background-color: #FAFAFA; 
                color: #888; 
                border: 1px solid #CCC; 
            }
            QComboBox QAbstractItemView { 
                background-color: #FFFFFF; 
                color: #333; 
                selection-background-color: #E0E0E0; 
                selection-color: #333; 
                border: 1px solid #CCC; 
            }
            QCheckBox {
                color: black;
                font: 14px Arial, sans-serif;
            }
            QLineEdit {
                color: black;
                font: 14px Arial, sans-serif;
                border: 1px solid #ccc;
                padding: 5px;
                background-color: #f0f0f0;
            }
            QGroupBox {
                font: 14px Arial, sans-serif;
                border: 1px solid #ccc;
                margin-top: 1em;
                background-color: #f0f0f0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QFormLayout {
                margin: 5px;
                border: 1px solid #ccc;
                background-color: #f0f0f0;
            }
            QWidget {
                background-color: #f0f0f0;
            }
            QPushButton {
                background-color: #FFFFFF;
                border: 1px solid #CCC;
                padding: 5px;
                font: 14px Arial, sans-serif;
                color: #333;
            }
            QPushButton:hover {
                background-color: #EDEDED;
            }
            QPushButton:checked {
                background-color: #E5E5E5;
            }
            QRadioButton {
                color: black;
                font: 14px Arial, sans-serif;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
            QRadioButton::indicator:checked {
                image: url(your_checked_image_here.png);
            }
            QRadioButton::indicator:unchecked {
                image: url(your_unchecked_image_here.png);
            }
        """)
        
        self.update_preview()

    def update_preview(self):
        if self.include_all_checkbox.isChecked():
            self.paths = self.get_all_paths()
        else:
            self.paths = self.original_paths.copy()

        if self.rename_worker:
            self.rename_worker.terminate()

        self.rename_worker = RenameWorker(self.paths, self.get_values())
        self.rename_worker.preview_updated.connect(self.display_preview)
        self.rename_worker.start()
        
    def get_all_paths(self) -> list:
        directory = path.dirname(self.paths[0])
        return [path.join(directory, item) for item in listdir(directory)]

    def display_preview(self, preview_data: list):
        self.preview_list.clear()
        for original, new_name in preview_data:
            self.preview_list.addItem(f"{original} -> {new_name}")

    def get_values(self) -> dict:
        return {
            "search": self.search_edit.text(),
            "replace": self.replace_edit.text(),
            "use_regex": self.regex_checkbox.isChecked(),
            "match_all": self.match_all_checkbox.isChecked(),
            "case_sensitive": self.case_sensitive_checkbox.isChecked(),
            "apply_to": self.apply_to_combo.currentText(),
            "include_subfolders": self.include_subfolders_button.isChecked(),
            "enumerate": self.enumerate_items_button.isChecked(),
            "formatting": "lowercase" if self.lowercase_button.isChecked() else 
                          "uppercase" if self.uppercase_button.isChecked() else 
                          "titlecase" if self.titlecase_button.isChecked() else 
                          "capitalize" if self.capitalize_button.isChecked() else None
        }
       
    def closeEvent(self, event: QEvent):
        if self.rename_worker:
            self.rename_worker.terminate()
        return super().closeEvent(event) 

