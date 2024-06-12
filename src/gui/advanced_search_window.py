from ..core.file_search_thread import FileSearchThread

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QToolButton, QGroupBox, QLineEdit, QPushButton, QHBoxLayout,
    QCheckBox, QDateTimeEdit, QComboBox, QSpinBox, QGridLayout, QLabel
)
from PySide6.QtCore import Qt, QDate

class AdvancedSearchWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Advanced Search")
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.resize(700, 450)

        layout = QVBoxLayout()
        
        # File Name Group
        file_name_group = QGroupBox("File Name: ")
        file_name_group_layout = QVBoxLayout()
        
        self.file_name_lineedit = QLineEdit()
        self.file_name_regex_checkbox = QCheckBox("Regular Expression")
        
        file_name_group_layout.addWidget(self.file_name_lineedit)
        file_name_group_layout.addWidget(self.file_name_regex_checkbox)
        file_name_group.setLayout(file_name_group_layout)
        layout.addWidget(file_name_group)
        
        # Search in Group
        search_in_group = QGroupBox("Search in: ")
        search_in_group_layout = QHBoxLayout()
        
        self.path_lineedit = QLineEdit()
        self.autofill_button = QPushButton("Autofill Paths")
        
        # Dropdown for common paths
        self.common_paths_combobox = QComboBox()
        self.common_paths_combobox.addItems(["All Local Drives", "All Drives", "Active Path", "All Open Tab Paths"])
        
        search_in_group_layout.addWidget(self.path_lineedit)
        search_in_group_layout.addWidget(self.autofill_button)
        search_in_group_layout.addWidget(self.common_paths_combobox)

        # Ignore options
        ignore_options_layout = QVBoxLayout()
        self.ignore_system_checkbox = QCheckBox("Ignore System Files")
        self.ignore_hidden_checkbox = QCheckBox("Ignore Hidden Files")
        self.ignore_system_hidden_checkbox = QCheckBox("Ignore System and Hidden Files")
        
        ignore_options_layout.addWidget(self.ignore_system_checkbox)
        ignore_options_layout.addWidget(self.ignore_hidden_checkbox)
        ignore_options_layout.addWidget(self.ignore_system_hidden_checkbox)
        
        search_in_group_layout.addLayout(ignore_options_layout)
        
        search_in_group.setLayout(search_in_group_layout)
        layout.addWidget(search_in_group)
        
        # Timestamp Specifier and Attribute Filter Group
        timestamp_attr_group = QGroupBox("Timestamp and Attributes: ")
        timestamp_attr_group_layout = QVBoxLayout()
        
        # Timestamp filter
        self.apply_date_filter_checkbox = QCheckBox("Apply Date Filter")
        self.date_filter_combobox = QComboBox()
        self.date_filter_combobox.addItems(["Between Dates", "Older Than", "Newer Than"])
        
        self.start_date_checkbox = QCheckBox("Specify Start Date")
        self.start_date = QDateTimeEdit()
        
        self.end_date_checkbox = QCheckBox("Specify End Date")
        self.end_date = QDateTimeEdit()
        
        self.duration_checkbox = QCheckBox("Specify Duration")
        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(1, 1000)
        self.duration_unit_combobox = QComboBox()
        self.duration_unit_combobox.addItems(["Minutes", "Hours", "Days", "Weeks", "Months", "Years"])

        self.date_type_combobox = QComboBox()
        self.date_type_combobox.addItems(["Date Accessed", "Date Created", "Date Modified"])
        
        timestamp_attr_group_layout.addWidget(self.apply_date_filter_checkbox)
        timestamp_attr_group_layout.addWidget(self.date_filter_combobox)
        timestamp_attr_group_layout.addWidget(self.start_date_checkbox)
        timestamp_attr_group_layout.addWidget(self.start_date)
        timestamp_attr_group_layout.addWidget(self.end_date_checkbox)
        timestamp_attr_group_layout.addWidget(self.end_date)
        timestamp_attr_group_layout.addWidget(self.duration_checkbox)
        timestamp_attr_group_layout.addWidget(QLabel("Duration:"))
        timestamp_attr_group_layout.addWidget(self.duration_spinbox)
        timestamp_attr_group_layout.addWidget(self.duration_unit_combobox)
        timestamp_attr_group_layout.addWidget(QLabel("Apply to:"))
        timestamp_attr_group_layout.addWidget(self.date_type_combobox)
        
        # Attributes filter
        attributes_layout = QGridLayout()
        
        self.attributes = {
            "Read Only": QCheckBox("Read Only"),
            "Archive": QCheckBox("Archive"),
            "Directory": QCheckBox("Directory"),
            "Encrypted": QCheckBox("Encrypted"),
            "Compressed": QCheckBox("Compressed"),
            "Hidden": QCheckBox("Hidden"),
            "System": QCheckBox("System")
        }
        
        for i, (attr_name, checkbox) in enumerate(self.attributes.items()):
            checkbox.setTristate(True)
            attributes_layout.addWidget(checkbox, i // 2, i % 2)
        
        timestamp_attr_group_layout.addLayout(attributes_layout)
        
        timestamp_attr_group.setLayout(timestamp_attr_group_layout)
        layout.addWidget(timestamp_attr_group)
        
        # File and Folder Filters Group
        filters_group = QGroupBox("File and Folder Filters: ")
        filters_group_layout = QVBoxLayout()
        
        self.include_filter_lineedit = QLineEdit()
        self.include_filter_regex_checkbox = QCheckBox("Regular Expression")
        self.exclude_filter_lineedit = QLineEdit()
        self.exclude_filter_regex_checkbox = QCheckBox("Regular Expression")
        
        filters_group_layout.addWidget(QLabel("Include:"))
        filters_group_layout.addWidget(self.include_filter_lineedit)
        filters_group_layout.addWidget(self.include_filter_regex_checkbox)
        filters_group_layout.addWidget(QLabel("Exclude:"))
        filters_group_layout.addWidget(self.exclude_filter_lineedit)
        filters_group_layout.addWidget(self.exclude_filter_regex_checkbox)
        
        filters_group.setLayout(filters_group_layout)
        layout.addWidget(filters_group)
        
        self.setLayout(layout)
