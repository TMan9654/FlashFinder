
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QPushButton

class BreadcrumbButton(QPushButton):
    itemsDropped = Signal(list)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            file_paths = [url.toLocalFile() for url in event.mimeData().urls()]
            self.itemsDropped.emit(file_paths)
