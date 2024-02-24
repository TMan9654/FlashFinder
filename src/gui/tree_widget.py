
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QTreeWidget


class TreeWidget(QTreeWidget):
    itemMoved = Signal()

    def dropEvent(self, event):
        super().dropEvent(event)
        self.itemMoved.emit()
        
    def focusOutEvent(self, event):
        self.clearSelection()
        super().focusOutEvent(event)

