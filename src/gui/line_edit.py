
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox

class LineEdit(QComboBox):
    escapedPressed = Signal()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.escapedPressed.emit()
        super().keyPressEvent(event)

