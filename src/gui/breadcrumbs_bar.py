from .breadcrumb_button import BreadcrumbButton

from os import path
from functools import partial

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QStackedWidget, QLineEdit, QSizePolicy, QFrame

class BreadcrumbsBar(QWidget):
    NavigateTo = Signal(str)
    OpenFile = Signal(str)
    FilesDropped = Signal(list, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._resize_timer = None
        self.setMinimumWidth(30)
        
        self.layout = QHBoxLayout(self)
        self.stacked_widget = QStackedWidget(self)
        self.stacked_widget.setFixedHeight(30)
        
        # Breadcrumbs view
        self.breadcrumb_widget = QWidget(self)
        self.breadcrumb_widget.setFixedHeight(30)
        self.breadcrumb_widget.setObjectName("breadcrumb_widget")        
        self.breadcrumb_layout = QHBoxLayout(self.breadcrumb_widget)
        self.breadcrumb_layout.setContentsMargins(0, 0, 0, 0)
        self.breadcrumb_layout.setSpacing(1)
        self.buttons: list[BreadcrumbButton] = []
        self.breadcrumb_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # QLineEdit view
        self.line_edit = QLineEdit(self)
        self.line_edit.setFixedHeight(30)
        self.line_edit.returnPressed.connect(self.update_from_line_edit)
        self.line_edit.editingFinished.connect(self.switch_to_breadcrumbs)
        self.line_edit.setObjectName("AddressBarEdit")
        
        self.stacked_widget.addWidget(self.breadcrumb_widget)
        self.stacked_widget.addWidget(self.line_edit)
        
        self.layout.addWidget(self.stacked_widget)
        self.setLayout(self.layout)
        
        self.stacked_widget.setCurrentIndex(0)
        self.breadcrumb_widget.mousePressEvent = self.switch_to_line_edit

    def set_path(self, file_path: str):
        self._pending_path = file_path
        self.adjust_breadcrumbs()

    def adjust_breadcrumbs(self):
        for btn in self.buttons:
            btn.deleteLater()
        self.buttons.clear()

        file_path = self._pending_path
        segments = file_path.split(path.sep)
        current_path = ""

        total_width = 0
        new_buttons = []

        for segment in segments:
            if current_path:
                current_path = current_path + f"\\{segment}"
            else:
                current_path = segment
            btn = BreadcrumbButton(segment, self)
            btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            command = partial(self.navigate_to, current_path)
            btn.clicked.connect(command)
            btn.itemsDropped.connect(partial(self.emit_file_drop, destination_path=current_path))
            btn.adjustSize()
            total_width += btn.width() + self.breadcrumb_layout.spacing()
            new_buttons.append(btn)

        available_width = self.breadcrumb_widget.width()
        if total_width > available_width:
            dots_btn = BreadcrumbButton("...", self)
            dots_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            dots_btn.adjustSize()
            dots_btn.clicked.connect(self.switch_to_line_edit)
            total_width += dots_btn.width() + self.breadcrumb_layout.spacing()
            self.breadcrumb_layout.addWidget(dots_btn)
            self.buttons.append(dots_btn)

        while total_width > available_width and new_buttons:
            btn_to_remove = new_buttons.pop(0)
            total_width -= (btn_to_remove.width() + self.breadcrumb_layout.spacing())
            btn_to_remove.deleteLater()

        for index, btn in enumerate(new_buttons):
            self.breadcrumb_layout.addWidget(btn)
            self.buttons.append(btn)

            if index < len(new_buttons) - 1:
                separator = QFrame(self)
                separator.setFrameShape(QFrame.VLine)
                separator.setFrameShadow(QFrame.Plain)
                separator.setStyleSheet("QFrame { background-color: #D9D9D9; width: 0px; }")
                self.breadcrumb_layout.addWidget(separator)
                self.buttons.append(separator)

        self.line_edit.setText(file_path)

    def emit_file_drop(self, source_paths, destination_path):
        self.FilesDropped.emit(source_paths, destination_path)

    def navigate_to(self, file_path: str):
        self.NavigateTo.emit(file_path)

    def switch_to_breadcrumbs(self):
        self.set_path(self.line_edit.text())
        self.stacked_widget.setCurrentIndex(0)
  
    def switch_to_line_edit(self, event):
        self.stacked_widget.setCurrentIndex(1)
        self.line_edit.setFocus()
        self.line_edit
        
    def update_from_line_edit(self):
        address = self.line_edit.text()
        self.set_path(address)
        if path.isdir(address):
            self.NavigateTo.emit(address)
        else:
            self.OpenFile.emit(address)

    def text(self):
        return self.line_edit.text()

