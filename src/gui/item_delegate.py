
from PySide6.QtWidgets import QStyledItemDelegate

class ItemDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        size.setHeight(20)
        return size
