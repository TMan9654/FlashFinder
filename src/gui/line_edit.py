
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox

class LineEdit(QComboBox):
    escapedPressed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaxVisibleItems(10)
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.escapedPressed.emit()
        super().keyPressEvent(event)

