from .general_settings import GeneralSettings
from .compare_settings import CompareSettings
from .search_settings import SearchSettings
from .about import About
from .help import Help

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QTabWidget, QVBoxLayout

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.resize(700, 450)

        self.tab_widget = QTabWidget(self)
        
        general_settings = GeneralSettings()
        compare_settings = CompareSettings()
        search_settings = SearchSettings()
        about_settings = About()
        help_settings = Help()

        self.tab_widget.addTab(general_settings, "General")
        self.tab_widget.addTab(compare_settings, "Compare")
        self.tab_widget.addTab(search_settings, "Search")
        self.tab_widget.addTab(about_settings, "About")
        self.tab_widget.addTab(help_settings, "Help")

        layout = QVBoxLayout(self)
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
        self.setStyleSheet("""
            QDialog {
                color: black;
            }
            QLabel {
                color: black;
            }
            QSpinBox, QDoubleSpinBox {
                color: black;
            }
        """)

