
from time import sleep

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QProgressBar, QTextBrowser
from PySide6.QtCore import Slot

class ProgressWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyPDFCompare")
        self.resize(600, 500)
        
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.layout = QVBoxLayout()
        
        self.progressBar = QProgressBar()
        self.progressBar.setFixedHeight(32)
        self.progressBar.setTextVisible(True)
        self.progressBar.setMaximum(100)
        self.progressBar.setMinimum(0)
        self.progressBar.setValue(0)
        self.logArea = QTextBrowser()
        self.logArea.setReadOnly(True)
        
        self.layout.addWidget(self.progressBar)
        self.layout.addWidget(self.logArea)
        
        self.centralWidget.setLayout(self.layout)
        
        self.setStyleSheet("""
            QProgressBar {
                border: 1px solid #004a88;
                border-radius: 5px;
                text-align: center;
                color: #c8c8c8;
                background-color: #202020;
            }
            QProgressBar::chunk {
                background-color: #0075d5;
                width: 1px;
                border: 1px solid transparent;
                border-radius: 5px;
            }
        """)
        
    @Slot(int)
    def update_progress(self, progress):
        self.progressBar.setValue(progress)
        
    @Slot(str)
    def update_log(self, message):
        self.logArea.append(message)
    
    @Slot(int)
    def operation_complete(self, time):
        sleep(time)
        self.close()