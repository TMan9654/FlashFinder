from ..config.config import IS_DARK, VERSION, ICONS_PATH

from os import path
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QHBoxLayout, QSpacerItem, QSizePolicy, QPushButton, QLabel

class TitleBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(35)
        self.title_layout = QHBoxLayout(self)
        self.title_layout.setContentsMargins(0, 0, 0, 1)
        self.title_layout.setSpacing(1)
        self.title_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        spacer_item = QSpacerItem(10, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        settings_icon = QIcon(path.join(ICONS_PATH, "w_settings.png") if IS_DARK else path.join(ICONS_PATH, "b_settings.png"))
        self.settings_button = QPushButton(self)
        self.settings_button.setFixedSize(30, 30)
        self.settings_button.setIcon(settings_icon)
        self.settings_button.setObjectName("SettingsButton")
        self.settings_button.setIconSize(QSize(20, 20))
        self.settings_button.clicked.connect(parent.open_settings)

        self.title_label = QLabel(f"FlashFinder {VERSION.split('.')[0]}")
        self.title_label.setObjectName("TitleLabel")

        self.minimize_button = QPushButton("╼", self)
        font = self.minimize_button.font()
        font.setPixelSize(13)
        self.minimize_button.setFont(font)
        self.minimize_button.setObjectName("MinimizeButton")
        self.minimize_button.setFixedSize(45, 34)
        self.minimize_button.clicked.connect(parent.showMinimized)

        self.maximize_restore_button = QPushButton(self)
        self.maximize_restore_button.setFixedSize(45, 34)
        self.maximize_restore_button.setObjectName("MaximizeButton")
        self.maximize_restore_button.clicked.connect(parent.set_geometry)

        self.close_button = QPushButton("X", self)
        self.close_button.setFont(font)
        self.close_button.setObjectName("CloseButton")
        self.close_button.setFixedSize(45, 34)
        self.close_button.clicked.connect(parent.cleanup)
        
        self.title_layout.addItem(spacer_item)
        self.title_layout.addWidget(self.title_label)
        self.title_layout.addItem(spacer_item)
        self.title_layout.addWidget(self.settings_button)
        self.title_layout.addWidget(self.minimize_button)
        self.title_layout.addWidget(self.maximize_restore_button)
        self.title_layout.addWidget(self.close_button)

