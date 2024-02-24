
from .config.config import ICONS_PATH
from .flashfinder import FlashFinder

from os import path
from sys import argv, exit
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import QApplication, QSplashScreen, QMessageBox

def launch_flashfinder():
    # ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("maxfield.tools.explorer.V7")
##    Used to set the process id for taskbar grouping purposes, uncomment if this breaks the grouping
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, False)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    app = QApplication(argv)
    pixmap = QPixmap(path.join(ICONS_PATH, "splash_screen.jpg")).scaled(960, 520, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    splash = QSplashScreen(pixmap)
    splash.show()
    app.setWindowIcon(QIcon(path.join(ICONS_PATH, "app.ico")))
    explorer = FlashFinder(app)
    app.aboutToQuit.connect(explorer.cleanup)
    splash.finish(explorer)
    try:
        exit(app.exec())
    except Exception as e:
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Icon.Critical)
        error_dialog.setText("An error occurred!")
        error_dialog.setInformativeText(str(e))
        error_dialog.setWindowTitle("Error")
        error_dialog.exec_()
    finally:
        explorer.indexer.stop()
