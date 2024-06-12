
from ...config.config import INDEXES_PATH, SETTINGS_PATH, COMPUTERNAME
from ...utils.utils import load_settings, save_settings

from os import path
from functools import partial
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QCheckBox, QLabel, QLineEdit, QPushButton, QGroupBox, \
    QVBoxLayout, QHBoxLayout, QRadioButton, QButtonGroup

class SearchSettings(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.indexer_running_file = path.join(INDEXES_PATH, f"{COMPUTERNAME}_indexer_running")
        self.search_settings = load_settings("search")
        self.INCLUDE_SUBFOLDERS = self.search_settings.get("INCLUDE_SUBFOLDERS")
        self.EXCLUDE_PATHS = self.search_settings.get("EXCLUDE_PATHS")
        self.INDEXED_SEARCH = self.search_settings.get("INDEXED_SEARCH")
        self.CACHED_SEARCH = self.search_settings.get("CACHED_SEARCH")
        self.HISTORY_LIFETIME = self.search_settings.get("HISTORY_LIFETIME")
        self.init_ui()

    def init_ui(self):
        self.include_subfolders_checkbox = QCheckBox('Include subfolders in search results when using "Search Current Path"')
        self.include_subfolders_checkbox.setChecked(self.INCLUDE_SUBFOLDERS)
        self.include_subfolders_checkbox.stateChanged.connect(self.include_subfolders)
        
        self.search_history_label = QLabel("Search History Lifetime: ")
        self.search_history_label.setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.search_history_buttons = QWidget()
        search_history_button_group = QButtonGroup()
        periods = ["0 days", "1 day", "2 days", "3 days", "5 days", "30 days", "60 days", "90 days"]
        button_group_layout = QHBoxLayout()
        for period in periods:
            time = int(period.split(" ")[0])
            radio_button = QRadioButton(period)
            if time == self.HISTORY_LIFETIME / 86400:
                radio_button.setChecked(True)
            radio_button.setFixedHeight(20)
            button_func = partial(self.set_history_lifetime, time)
            radio_button.clicked.connect(button_func)
            button_group_layout.addWidget(radio_button)
            search_history_button_group.addButton(radio_button)
        search_history_button_group.setExclusive(True)
        self.search_history_buttons.setLayout(button_group_layout)

        self.exclude_paths_label = QLabel("Excluded indexer paths: ")
        self.exclude_paths_label.setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.exclude_paths_lineedit = QLineEdit()
        self.exclude_paths_lineedit.setText(str(self.EXCLUDE_PATHS))
        self.exclude_paths_lineedit.textEdited.connect(self.set_excluded_paths)
        
        self.indexed_search_checkbox = QCheckBox("Use indexes when searching\n(Searches will be faster but might not be the most up-to-date.)")
        self.indexed_search_checkbox.setChecked(self.INDEXED_SEARCH)
        self.indexed_search_checkbox.stateChanged.connect(self.indexed_search)
        
        self.cache_indexes_checkbox = QCheckBox("Cache indexes for searching\n(Searches will be faster but results in signifcantly greater memory usage. [~750MB of RAM per 1,000,000 indexed files])")
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
        general_group_layout.addWidget(self.search_history_label)
        general_group_layout.addWidget(self.search_history_buttons)
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
        # self.setStyleSheet("""
        #     QLabel {
        #         color: black;
        #         font: 14px Arial, sans-serif;
        #     }
        #     QSpinBox {
        #         color: black;
        #         font: 14px Arial, sans-serif;
        #         border: 1px solid #ccc;
        #         padding: 5px;
        #         background-color: #f0f0f0;
        #     }
        #     QComboBox { 
        #         background-color: #FFFFFF; 
        #         color: #333; 
        #         font: 14px Arial, sans-serif;
        #         border: 1px solid #CCC; 
        #     }
        #     QComboBox:hover { 
        #         background-color: #EDEDED; 
        #     }
        #     QComboBox:focus { 
        #         background-color: #E5E5E5; 
        #     }
        #     QComboBox:disabled { 
        #         background-color: #FAFAFA; 
        #         color: #888; 
        #         border: 1px solid #CCC; 
        #     }
        #     QComboBox QAbstractItemView { 
        #         background-color: #FFFFFF; 
        #         color: #333; 
        #         selection-background-color: #E0E0E0; 
        #         selection-color: #333; 
        #         border: 1px solid #CCC; 
        #     }
        #     QCheckBox {
        #         color: black;
        #         font: 14px Arial, sans-serif;
        #     }
        #     QLineEdit {
        #         color: black;
        #         font: 14px Arial, sans-serif;
        #         border: 1px solid #ccc;
        #         padding: 5px;
        #         background-color: #f0f0f0;
        #     }
        #     QGroupBox {
        #         font: 14px Arial, sans-serif;
        #         border: 1px solid #ccc;
        #         margin-top: 1em;
        #         background-color: #f0f0f0;
        #     }
        #     QGroupBox::title {
        #         subcontrol-origin: margin;
        #         left: 10px;
        #         padding: 0 3px 0 3px;
        #     }
        #     QFormLayout {
        #         margin: 5px;
        #         border: 1px solid #ccc;
        #         background-color: #f0f0f0;
        #     }
        #     QWidget {
        #         background-color: #f0f0f0;
        #     }
        #     QPushButton {
        #         background-color: #f0f0f0;
        #         color: black;
        #         border: 2px solid #ED1D24;
        #         padding: 3px 5px;
        #         text-align: center;
        #         text-decoration: none;
        #         font-size: 14px;
        #         margin: 4px 2px;
        #         border-radius: 4px;
        #     }
        # """)

    def include_subfolders(self, state: int):
        if state == 2:
            self.search_settings["INCLUDE_SUBFOLDERS"] = True
        else:
            self.search_settings["INCLUDE_SUBFOLDERS"] = False
        save_settings("search", self.search_settings)

    def set_excluded_paths(self, paths: list):
        if paths:
            self.search_settings["EXCLUDE_PATHS"] = list(paths)
        save_settings("search", self.search_settings)
        
    def set_history_lifetime(self, time: int):
        if time:
            self.search_settings["HISTORY_LIFETIME"] = time * 86400
        save_settings("search", self.search_settings)

    def indexed_search(self, state: int):
        if state == 2:
            self.search_settings["INDEXED_SEARCH"] = True
        else:
            self.search_settings["INDEXED_SEARCH"] = False
        save_settings("search", self.search_settings)
        
    def cached_search(self, state: int):
        if state == 2:
            self.search_settings["CACHED_SEARCH"] = True
            with open(self.indexer_running_file, "w") as f:
                f.write("Caching...")
        else:
            self.search_settings["CACHED_SEARCH"] = False
            with open(self.indexer_running_file, "w") as f:
                f.write("Clearing Cache...")
        save_settings("search", self.search_settings)

    def rebuild_index(self):
        rebuild_signal_path = path.join(SETTINGS_PATH, f"{COMPUTERNAME}_rebuild")
        with open(rebuild_signal_path, "w") as f:
            f.write("Rebuild Signalled")
