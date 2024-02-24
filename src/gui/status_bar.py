
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

class StatusBar(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setText("Ready")

        self.setFixedHeight(20)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
