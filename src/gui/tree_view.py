
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QTreeView, QAbstractItemView
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent


class TreeView(QTreeView):
    dropAccepted = Signal(list, bool)

    def __init__(self, parent=None):
        super(TreeView, self).__init__(parent)
        self.startDragPosition = None
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        mime = event.mimeData()
        if mime.hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        mime = event.mimeData()
        if mime.hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        mime = event.mimeData()
        if mime.hasUrls():
            is_internal_drop = event.source() == self
            urls = [url.toLocalFile() for url in mime.urls()]
            event.acceptProposedAction()
            self.dropAccepted.emit(urls, is_internal_drop)
