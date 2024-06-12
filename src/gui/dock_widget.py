
from PySide6.QtCore import QRect, Signal
from PySide6.QtWidgets import QDockWidget, QTextEdit, QSizePolicy

class DockWidget(QDockWidget):
    sizeChanged = Signal()

    def __init__(self, title, parent=None):
        super(DockWidget, self).__init__(parent)
        self.title = title
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.textEdit = QTextEdit(self)
        self.textEdit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setWidget(self.textEdit)


