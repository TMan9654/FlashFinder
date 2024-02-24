
from PySide6.QtCore import Qt, Signal, QTimer, QEvent
from PySide6.QtWidgets import QTabWidget, QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy, QWidget, QInputDialog

class TabWidget(QTabWidget):
    buttonPressed = Signal()

    def __init__(self, parent=None):
        super().__init__()
        self.setObjectName("CustomTabWidget")
        self.tabBar().setObjectName("MainTabBar")
        self.tabBar().setAcceptDrops(True)
        self.tabBar().installEventFilter(self)
        self.new_tab_button = QPushButton("+")
        self.new_tab_button.clicked.connect(self.buttonPressed.emit)
        self.new_tab_button.setFixedSize(20, 20)
        self.new_tab_button.setObjectName("NewTabButton")
        corner_layout = QHBoxLayout()
        corner_layout.setContentsMargins(0, 0, 0, 0)
        corner_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        corner_layout.addWidget(self.new_tab_button)
        corner_widget = QWidget()
        corner_widget.setLayout(corner_layout)
        self.setCornerWidget(corner_widget, Qt.Corner.TopRightCorner)
        
        self.switch_timer = QTimer(self)
        self.switch_timer.setSingleShot(True)
        self.switch_timer.timeout.connect(self.switch_tab)

    def eventFilter(self, event_object, event):
        if event_object == self.tabBar() and event.type() == QEvent.DragEnter:
            event.accept()
            return True
        elif event_object == self.tabBar() and event.type() == QEvent.DragMove:
            index = self.tabBar().tabAt(event.pos())
            if not self.switch_timer.isActive():
                self.switch_timer.start(1500)
                self.switch_to = index
            return True
        elif event_object == self.tabBar() and event.type() == QEvent.Drop:
            event.accept()
            return True
        elif event_object == self.tabBar() and event.type() == QEvent.MouseButtonDblClick:
            index = self.tabBar().tabAt(event.pos())
            if index >= 0:
                self.rename_tab(index)
            return True
        return super().eventFilter(event_object, event)
    
    def switch_tab(self):
        self.setCurrentIndex(self.switch_to)

    def rename_tab(self, index):
        current_name = self.tabText(index)
        new_name, ok = QInputDialog.getText(self, "Rename Tab", "Enter new name:", text=current_name)
        if ok and new_name:
            self.parent().browser_history[new_name] = self.parent().browser_history[current_name]
            self.parent().browser_history.pop(current_name)
            self.parent().browser_forward_history[new_name] = self.parent().browser_forward_history[current_name]
            self.parent().browser_forward_history.pop(current_name)
            self.setTabText(index, new_name)

