
from PySide6.QtCore import QRect, Signal
from PySide6.QtWidgets import QDockWidget, QTextEdit, QSizePolicy, QMainWindow

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

    # def resizeEvent(self, event):
    #     self.sizeChanged.emit()

    #     if isinstance(self.parent(), QMainWindow):
    #         mainWindow = self.parent()
    #         rightBound = mainWindow.geometry().right()
    #         bottomBound = mainWindow.geometry().bottom()

    #         if self.geometry().right() > rightBound:
    #             newLeft = rightBound - self.width()
    #             self.setGeometry(QRect(newLeft, self.geometry().top(), self.width(), self.height()))
                
    #         if self.geometry().bottom() > bottomBound:
    #             self.setGeometry(QRect(self.geometry().left(), self.geometry().top(), self.width(), self.height() - (self.geometry().bottom() - bottomBound)))

    #     super(DockWidget, self).resizeEvent(event)

