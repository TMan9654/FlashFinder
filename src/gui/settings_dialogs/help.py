
from ...config.config import DOCS_PATH

from os import path
from PySide6.QtWidgets import QWidget, QGroupBox, QTextBrowser, QVBoxLayout


class Help(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        documentation_group = QGroupBox()
        self.documentation_browser = QTextBrowser()
        self.documentation_browser.setOpenExternalLinks(True)
        
        self.load_html_content(self.documentation_browser, path.join(DOCS_PATH, "main_menu.html"))

        changelog_group = QGroupBox()
        self.changelog_browser = QTextBrowser()
        self.changelog_browser.setOpenExternalLinks(True)
        
        self.load_html_content(self.changelog_browser, path.join(DOCS_PATH, "changelog.html"))

        main_layout = QVBoxLayout()
        documentation_group_layout = QVBoxLayout()
        changelog_group_layout = QVBoxLayout()

        documentation_group_layout.addWidget(self.documentation_browser)
        changelog_group_layout.addWidget(self.changelog_browser)

        main_layout.addWidget(documentation_group)
        main_layout.addWidget(changelog_group)

        documentation_group.setLayout(documentation_group_layout)
        changelog_group.setLayout(changelog_group_layout)
        self.setLayout(main_layout)

        # self.setStyleSheet("""
        #     QLabel {
        #         color: black;
        #         background-color: #ffffff;
        #         font: 14px Arial, sans-serif;
        #     }
        #     QWidget {
        #         background-color: #f0f0f0;
        #     }
        # """)

    def load_html_content(self, browser: QTextBrowser, filepath: str):
        if path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as file:
                html_content = file.read()
            browser.setHtml(html_content)
