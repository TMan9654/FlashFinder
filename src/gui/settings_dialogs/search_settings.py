
from ...config.config import INDEXES_PATH, SETTINGS_PATH, COMPUTERNAME

from os import path
from json import load, dump
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QCheckBox, QLabel, QLineEdit, QPushButton, QGroupBox, QVBoxLayout

class SearchSettings(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.indexer_running_file = path.join(INDEXES_PATH, f"{COMPUTERNAME}_indexer_running")
        self.search_settings_path = path.join(SETTINGS_PATH, f"{COMPUTERNAME}_search-settings.json")
        self.search_settings = self.load_settings()
        self.INCLUDE_SUBFOLDERS = self.search_settings.get("INCLUDE_SUBFOLDERS")
        self.EXCLUDE_PATHS = self.search_settings.get("EXCLUDE_PATHS")
        self.INDEXED_SEARCH = self.search_settings.get("INDEXED_SEARCH")
        self.CACHED_SEARCH = self.search_settings.get("CACHED_SEARCH")
        self.init_ui()

    def init_ui(self):
        self.include_subfolders_checkbox = QCheckBox('Include subfolders in search results when using "Search Current Path"')
        self.include_subfolders_checkbox.setChecked(self.INCLUDE_SUBFOLDERS)
        self.include_subfolders_checkbox.stateChanged.connect(self.include_subfolders)

        self.indexed_search_checkbox = QCheckBox("Use indexes when searching\n(Searches may be faster but might not be the most up-to-date.)")
        self.indexed_search_checkbox.setChecked(self.INDEXED_SEARCH)
        self.indexed_search_checkbox.stateChanged.connect(self.indexed_search)
        
        self.exclude_paths_label = QLabel("Excluded indexer paths: ")
        self.exclude_paths_label.setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.exclude_paths_lineedit = QLineEdit()
        self.exclude_paths_lineedit.setText(str(self.EXCLUDE_PATHS))
        self.exclude_paths_lineedit.textEdited.connect(self.set_excluded_paths)
        
        self.cache_indexes_checkbox = QCheckBox("Cache indexes for searching\n(Searches may be faster but results in signifcantly greater memory usage. [~750MB of RAM per 1,000,000 indexed files])")
        self.cache_indexes_checkbox.setChecked(self.CACHED_SEARCH)
        self.cache_indexes_checkbox.stateChanged.connect(self.cached_search)
        
        self.rebuild_index_button = QPushButton("Rebuild Index")
        self.rebuild_index_button.clicked.connect(self.rebuild_index)

        general_group = QGroupBox("General")
        how_to_search_group = QGroupBox("How to search")
        
        general_group_layout = QVBoxLayout(general_group)
        how_to_search_group_layout = QVBoxLayout(how_to_search_group)
        main_layout = QVBoxLayout(self)

        general_group_layout.addWidget(self.include_subfolders_checkbox)
        general_group_layout.addWidget(self.exclude_paths_label)
        general_group_layout.addWidget(self.exclude_paths_lineedit)
        how_to_search_group_layout.addWidget(self.indexed_search_checkbox)
        how_to_search_group_layout.addWidget(self.cache_indexes_checkbox)
        main_layout.addWidget(general_group)
        main_layout.addWidget(how_to_search_group)
        main_layout.addWidget(self.rebuild_index_button)

        general_group.setLayout(general_group_layout)
        how_to_search_group.setLayout(how_to_search_group_layout)
        self.setLayout(main_layout)
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
                background-color: #f0f0f0;
                color: black;
                border: 2px solid #ED1D24;
                padding: 3px 5px;
                text-align: center;
                text-decoration: none;
                font-size: 14px;
                margin: 4px 2px;
                border-radius: 4px;
            }
        """)

    def include_subfolders(self, state: int):
        if state == 2:
            self.INCLUDE_SUBFOLDERS = True
        else:
            self.INCLUDE_SUBFOLDERS = False
        self.save_settings()

    def set_excluded_paths(self, paths: list):
        if paths:
            self.EXCLUDE_PATHS = list(paths)
        self.save_settings()

    def indexed_search(self, state: int):
        if state == 2:
            self.INDEXED_SEARCH = True
        else:
            self.INDEXED_SEARCH = False
        self.save_settings()
        
    def cached_search(self, state: int):
        if state == 2:
            self.CACHED_SEARCH = True
            with open(self.indexer_running_file, "w") as f:
                f.write("Caching...")
        else:
            self.CACHED_SEARCH = False
            with open(self.indexer_running_file, "w") as f:
                f.write("Clearing Cache...")
        self.save_settings()

    def load_settings(self) -> dict:
        default_settings = {
            "INCLUDE_SUBFOLDERS": True,
            "EXCLUDE_PATHS": ["$Recycle.Bin", "$RECYCLE.BIN", "System Volume Information", "Windows", "Program Files", "Program Files (x86)", "ProgramData", "Recovery"],
            "INDEXED_SEARCH": True,
            "CACHED_SEARCH": True
        }

        if path.exists(self.search_settings_path):
            with open(self.search_settings_path, "r") as f:
                search_settings = load(f)
            updated = False
            for key, value in default_settings.items():
                if key not in search_settings:
                    search_settings[key] = value
                    updated = True

            if updated:
                with open(self.search_settings_path, "w") as f:
                    dump(search_settings, f, indent=4)
        else:
            search_settings = default_settings
            with open(self.search_settings_path, "w") as f:
                dump(search_settings, f, indent=4)

        return search_settings

    def save_settings(self):
        self.search_settings = {
            "INDEXED_SEARCH": self.INDEXED_SEARCH,
            "EXCLUDE_PATHS": self.EXCLUDE_PATHS,
            "INCLUDE_SUBFOLDERS": self.INCLUDE_SUBFOLDERS,
            "CACHED_SEARCH": self.CACHED_SEARCH
        }
        try:
            with open(self.search_settings_path, "w") as f:
                dump(self.search_settings, f, indent=4)
        except PermissionError:
            self.save_settings()

    def rebuild_index(self):
        rebuild_signal_path = path.join(SETTINGS_PATH, f"{COMPUTERNAME}_rebuild")
        with open(rebuild_signal_path, "w") as f:
            f.write("Rebuild Signalled")

