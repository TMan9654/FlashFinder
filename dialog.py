from PyQt5.QtWidgets import QApplication, QDialog, QLabel
from PyQt5.QtGui import QIcon
import os

class UpdateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Update Notice")
        self.setWindowIcon(QIcon(os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons"), "app.ico")))
        
        self.label = QLabel(f"Flashfinder has been update!", self)
        self.resize(300, 50)


if __name__ == "__main__":
    app = QApplication()
    dialog = UpdateDialog()
    dialog.show()
    app.exec_()