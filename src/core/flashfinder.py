
from ..config.config import BASE_PATH, INDEXES_PATH, ICONS_PATH, SETTINGS_PATH, TEMP_PATH, VERSION, \
    IS_DARK, COMPUTERNAME, DESKTOP_PATH, DOCUMENTS_PATH, PICTURES_PATH

from .status_check_thread import StatusCheckThread
from .file_process_thread import FileProcessThread
from .compare_thread import CompareThread
from .file_search_thread import FileSearchThread
from .file_indexer import FileIndexer

from ..gui.title_bar import TitleBar
from ..gui.tree_view import TreeView
from ..gui.tree_widget import TreeWidget
from ..gui.tab_widget import TabWidget
from ..gui.breadcrumbs_bar import BreadcrumbsBar
from ..gui.line_edit import LineEdit
from ..gui.item_delegate import ItemDelegate
from ..gui.dock_widget import DockWidget
from ..gui.preview_window import PreviewWindow
from ..gui.status_bar import StatusBar
from ..gui.file_replace_dialog import FileReplaceDialog
from ..gui.power_rename_dialog import PowerRenameDialog
from ..gui.settings_dialogs.settings import SettingsDialog

from ..models.file_system_model import FileSystemModel

from ..utils.utils import fix_coordinate

from collections import OrderedDict
from send2trash import send2trash
from pythoncom import CoCreateInstance, CLSCTX_INPROC_SERVER, IID_IPersistFile
from win32com.shell import shell, shellcon
from win32api import GetLogicalDriveStrings
from win32file import GetDriveType, DRIVE_REMOTE
from os import path, remove, walk, startfile, makedirs, listdir, rename, mkdir, rmdir
from subprocess import Popen
from json import load, dump
from zipfile import ZipFile
from ctypes import wintypes
from time import time
from shutil import move, copytree, copy2
from win32security import GetFileSecurity, OWNER_SECURITY_INFORMATION, LookupAccountSid
from PySide6.QtCore import Qt, QTimer, QItemSelectionModel, QMimeData, QUrl, QPoint, QFileInfo, QSize
from PySide6.QtGui import QResizeEvent, QKeySequence, QIcon, QPixmap, QGuiApplication, QCursor, QAction, QShortcut
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QPushButton, QMessageBox, QTreeWidget, \
    QTreeWidgetItem, QHeaderView, QFileDialog, QMenu, QSplitter, QAbstractItemView, QFileIconProvider, QProgressBar, \
        QFormLayout, QTabBar, QLineEdit, QDockWidget, QToolBar, QInputDialog, QStatusBar, QDialog, QWidget, QSizePolicy, \
        QTreeView


class FlashFinder(QMainWindow):
    def __init__(self, parent):
        super().__init__()
        self.setMaximumSize(QGuiApplication.primaryScreen().availableSize())
        self.current_path = DESKTOP_PATH
        self.browser_history = {"Main": []}
        self.browser_forward_history = {"Main": []}
        self.search_history = OrderedDict()
        self.undo_history = []
        self.redo_history = []
        self.copied_path_item = ()
        self.last_clicked_timestamp = 0
        self.clipboard = parent.clipboard()
        self.pinned_items = {}
        self.is_maximized = False
        self.search_thread = None
        self.compare_thread = None
        self.is_dragging = False
        self.is_being_dragged = False
        self.tab_iterator = 0
        
        self.index_cache = {}
        self.indexer = FileIndexer()
        self.indexer.start()
        
        self.status_checker = StatusCheckThread(self)
        self.status_checker.statusChanged.connect(self.update_indexing_labels)
        self.status_checker.requestClose.connect(self.cleanup)
        self.status_checker.start()
        
        self.initUI()
        self.load_pinned_items()
        self.load_tabs()
        self.load_search_history()

    def initUI(self):
        self.setWindowTitle(f"FlashFinder {VERSION.split('.')[0]} by TerrinTech")
        self.setGeometry(480, 260, 960, 520) # 1920x1080: 960x520, 1650x1050: 840x504
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        self.title_bar = TitleBar(self)
        self.title_bar.setObjectName("TitleBar")
        self.setMenuWidget(self.title_bar)
        
        self.search_mode_icon = QIcon(path.join(ICONS_PATH, "w_all_drives.png") if IS_DARK is True else path.join(ICONS_PATH, "b_all_drives.png"))
        self.sidebar_button_icon = QIcon(QPixmap(path.join(ICONS_PATH, "w_menu.png") if IS_DARK is True else path.join(ICONS_PATH, "b_menu.png")).scaled(12, 12))
        self.preview_button_icon = QIcon(QPixmap(path.join(ICONS_PATH, "w_preview.png") if IS_DARK is True else path.join(ICONS_PATH, "b_preview.png")).scaled(14, 14))
        self.maximize_icon = QIcon(QPixmap(path.join(ICONS_PATH, "w_maximize.png") if IS_DARK is True else path.join(ICONS_PATH, "b_maximize.png")).scaled(14, 14))
        self.restore_icon = QIcon(QPixmap(path.join(ICONS_PATH, "w_minimize.png") if IS_DARK is True else path.join(ICONS_PATH, "b_minimize.png")).scaled(14, 14))
        
        self.setContentsMargins(5, 0, 5, 0)

        self.model = FileSystemModel()
        self.model.setRootPath("")

        self.main_view = TreeView(self)
        self.main_view.setModel(self.model)
        self.main_view.setRootIndex(self.model.index(DESKTOP_PATH))
        self.main_view.header().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.main_view.setSortingEnabled(True)
        self.main_view.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.main_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.main_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.main_view.setUniformRowHeights(True)
        self.main_view.setDragEnabled(True)
        self.main_view.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.main_view.dropAccepted.connect(self.handle_drop)

        self.main_view.clicked.connect(self.on_item_clicked)
        self.main_view.doubleClicked.connect(self.on_item_double_clicked)
        
        self.sidebar = QDockWidget("Quick Access", self)
        self.sidebar.setMinimumWidth(200)
        
        self.sidebar_widget = QWidget(self)

        self.quick_access_list = QTreeWidget()
        self.quick_access_list.setHeaderHidden(True)
        self.quick_access_list.setColumnHidden(1, True)
        self.quick_access_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        
        self.source = QTreeView()
        self.source.setModel(self.model)
        self.source.setHeaderHidden(True)
        self.source.setColumnHidden(1, True)
        self.source.setColumnHidden(2, True)
        self.source.setColumnHidden(3, True)
        self.source.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        
        self.pinned = TreeWidget()    
        self.pinned.setDragEnabled(True)
        self.pinned.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.pinned.setHeaderHidden(True)
        self.pinned.setColumnHidden(1, True)
        self.pinned.itemMoved.connect(self.save_pinned_items)

        self.quick_access_list.clicked.connect(self.on_quick_access_clicked)
        self.source.clicked.connect(self.on_source_item_clicked)
        self.pinned.clicked.connect(self.on_pinned_item_clicked)
        
        splitter = QSplitter(Qt.Orientation.Vertical, self.sidebar_widget)
        splitter.addWidget(self.quick_access_list)
        splitter.addWidget(self.source)
        splitter.addWidget(self.pinned)

        self.sidebar.setWidget(splitter)
        
        self.tab_widget = TabWidget()
        self.tab_widget.setMovable(True)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.buttonPressed.connect(self.add_new_tab)
        self.tab_widget.currentChanged.connect(self.update_address_bar)
        
        self.setCentralWidget(self.tab_widget)

        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.sidebar)

        self.search_time = 0.0
        self.search_result_count = 0
        
        self.search_results_dock = QDockWidget("Search Results", self)
        self.search_results_tree = QTreeWidget(self)
        self.search_results_tree.setHeaderLabels(["Name", "Type", "Path", "Date Created", "Date Modified"])
        self.search_results_tree.setColumnCount(5)
        self.search_results_tree.setSortingEnabled(True)
        self.search_results_tree.setRootIsDecorated(False)
        self.search_results_tree.sortByColumn(2, Qt.SortOrder.AscendingOrder)
        self.search_results_tree.header().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.main_view.setColumnWidth(0, 400)
        self.search_results_tree.header().setStretchLastSection(False)
        self.search_results_tree.itemClicked.connect(self.on_search_result_item_clicked)
        self.search_results_tree.itemDoubleClicked.connect(self.on_search_result_item_double_clicked)
        self.search_time = 0.0
        self.search_result_count = 0
        self.search_info_bar = QStatusBar(self.search_results_dock)
        self.search_info_bar.setFixedHeight(20)
        self.search_info_bar.setContentsMargins(0, 0, 0, 3)
        self.search_info_bar.setSizeGripEnabled(False)
        self.search_info_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.search_info_label = QLabel("", self)
        self.search_info_label.setObjectName("SearchInfoLabel")
        self.search_info_bar.addWidget(self.search_info_label)
        
        search_results_layout = QVBoxLayout()
        search_results_layout.addWidget(self.search_results_tree)
        search_results_layout.addWidget(self.search_info_bar)
        container_for_dock = QWidget(self)
        search_results_layout.setContentsMargins(2, 0, 2, 2)
        container_for_dock.setLayout(search_results_layout)
        self.search_results_dock.setWidget(container_for_dock)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, self.search_results_dock)
        self.search_results_dock.setVisible(False)
        self.search_results_dock.visibilityChanged.connect(self.resetProgressBar)

        self.main_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.main_view.customContextMenuRequested.connect(self.create_context_menu)

        self.pinned.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.pinned.customContextMenuRequested.connect(self.create_context_menu)

        self.search_results_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.search_results_tree.customContextMenuRequested.connect(self.create_context_menu)

        self.toolbar = QToolBar("Navigation", self)
        self.toolbar.setContentsMargins(0, 0, 0, 5)
        self.addToolBar(self.toolbar)
        
        self.back_button = QAction("🡰", self)
        self.back_button.setToolTip("Back")
        self.forward_button = QAction("🡲", self)
        self.forward_button.setToolTip("Forward")
        self.up_button = QAction("🡹", self)
        self.up_button.setToolTip("Up One Level")
        self.toolbar.addAction(self.back_button)
        self.toolbar.addAction(self.forward_button)
        self.toolbar.addAction(self.up_button)

        self.back_button.triggered.connect(self.go_back)
        self.forward_button.triggered.connect(self.go_forward)
        self.up_button.triggered.connect(self.go_up)
        
        self.address_bar = BreadcrumbsBar(self)
        self.address_bar.NavigateTo.connect(self.browse_folder)
        self.address_bar.OpenFile.connect(self.open_path)
        self.address_bar.FilesDropped.connect(self.move_item)

        self.search_bar = LineEdit(self)
        self.search_bar.setItemDelegate(ItemDelegate())
        self.search_bar.setEditable(True)
        self.search_bar.setFixedHeight(28)
        self.search_bar.lineEdit().setFixedHeight(28)
        self.search_bar.setMaxVisibleItems(10)
        self.search_bar.lineEdit().returnPressed.connect(self.start_searching)
        self.search_bar.escapedPressed.connect(self.stop_searching)
        self.search_bar.setPlaceholderText("Search All Drives")

        self.search_progress_bar = QProgressBar(self)
        self.search_progress_bar.setFixedHeight(2)
        self.search_progress_bar.setTextVisible(False)
        self.search_progress_bar.setMaximum(100)
        self.search_progress_bar.setMinimum(0)
        self.search_progress_bar.setValue(0)
        self.search_progress_bar.setProperty("completed", False)
        
        self.search_mode_button = QPushButton(self)
        self.search_mode_button.setIcon(self.search_mode_icon)
        self.search_mode_button.setFixedSize(28, 28)
        self.search_mode_button.setToolTip(self.search_bar.placeholderText())
        self.search_mode_button.clicked.connect(self.change_search_mode)
        self.search_mode_button.setObjectName("SearchModeButton")
        
        search_container = QWidget(self)
        search_layout = QVBoxLayout()
        search_container.setLayout(search_layout)

        search_layout.addWidget(self.search_bar)
        search_layout.addWidget(self.search_progress_bar)

        search_layout.setSpacing(0)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.toolbar.addWidget(self.address_bar)
        self.toolbar.addWidget(search_container)
        self.toolbar.addWidget(self.search_mode_button)
        
        self.bottom_toolbar = QToolBar("Info Bar", self)
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, self.bottom_toolbar)
        
        spacer = QWidget(self)
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.sidebar_button = QAction(self)
        self.sidebar_button.setIcon(self.sidebar_button_icon)
        self.sidebar_button.setToolTip("Quick Access")
        self.sidebar_button.triggered.connect(self.toggle_sidebar)

        self.preview_button = QAction(self)
        self.preview_button.setIcon(self.preview_button_icon)
        self.preview_button.setToolTip("Preview")
        self.preview_button.triggered.connect(self.toggle_preview)
        
        self.access = QPushButton("Read", self)
        self.access.setFixedWidth(40)
        self.access.setFixedHeight(30)
        self.access.clicked.connect(self.change_access)
        self.access.setObjectName("AccessButton")

        self.status_label = QLabel("Idle", self)
        self.status_label.setObjectName("StatusLabel")

        self.index_label = QLabel("Indexed Files: 0", self)
        self.index_label.setObjectName("IndexLabel")

        self.file_count_label = QLabel("File Count: 0", self)
        self.file_count_label.setObjectName("FileCountLabel")
        
        self.bottom_toolbar.addAction(self.sidebar_button)
        self.bottom_toolbar.addAction(self.preview_button)
        self.bottom_toolbar.addWidget(self.access)
        self.bottom_toolbar.addWidget(spacer)
        self.bottom_toolbar.addWidget(self.status_label)
        self.bottom_toolbar.addWidget(self.index_label)
        self.bottom_toolbar.addWidget(self.file_count_label)

        self.preview_dock = DockWidget("Preview", self)
        self.preview_dock.setVisible(False)
        self.preview_dock.setMinimumWidth(300)
        
        preview_layout = QVBoxLayout()
        
        self.preview = PreviewWindow(self)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.preview.setObjectName("PreviewWindow")
        
        self.details_bar = StatusBar()
        self.details_bar.setObjectName("DetailsBar")

        preview_layout.addWidget(self.preview)
        preview_layout.addWidget(self.details_bar)

        preview_container = QWidget()
        preview_container.setLayout(preview_layout)
        
        self.preview_dock.setWidget(preview_container)
        
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.preview_dock)
        self.preview_dock.sizeChanged.connect(self.preview.update_preview)
        
        self.main_view.selectionModel().selectionChanged.connect(self.update_address_bar)
        self.main_view.selectionModel().selectionChanged.connect(self.preview.update_preview)
        
        self.index_count = self.status_checker.get_index_count()
        
        self.active_shortcuts()
        self.update_indexing_labels("Idle", self.index_count, self.index_cache)
        self.populate_quick_access()
        self.apply_theme_stylesheet()
        self.show()
        self.update_address_bar()

    def active_shortcuts(self, current_view: TreeView=None):
        if not current_view:
            current_view = self.main_view

        # Main View
        self.copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), current_view)
        self.copy_shortcut.activated.connect(lambda: self.copy_item(list(set(self.model.filePath(index) for index in current_view.selectedIndexes())), "item"))
        
        self.copy_name_shortcut = QShortcut(QKeySequence("Shift+Alt+C"), current_view)
        self.copy_name_shortcut.activated.connect(lambda: self.copy_item(list(set(self.model.filePath(index) for index in current_view.selectedIndexes())), "basename"))

        self.copy_path_shortcut = QShortcut(QKeySequence("Ctrl+Shift+C"), current_view)
        self.copy_path_shortcut.activated.connect(lambda: self.copy_item(list(set(self.model.filePath(index) for index in current_view.selectedIndexes())), "path"))

        self.copy_current_path_shortcut = QShortcut(QKeySequence("Ctrl+Alt+C"), current_view)
        self.copy_current_path_shortcut.activated.connect(lambda: self.copy_item(list(set(self.model.filePath(index) for index in current_view.selectedIndexes())), "current path"))

        self.paste_shortcut = QShortcut(QKeySequence("Ctrl+V"), current_view)
        self.paste_shortcut.activated.connect(self.paste_item)

        self.move_shortcut = QShortcut(QKeySequence("Ctrl+M"), current_view)
        self.move_shortcut.activated.connect(lambda: self.move_item(list(set(self.model.filePath(index) for index in current_view.selectedIndexes()))))

        self.rename_shortcut = QShortcut(QKeySequence("Ctrl+R"), current_view)
        self.rename_shortcut.activated.connect(lambda: self.rename_item(self.model.filePath(current_view.currentIndex())))

        self.delete_shortcut = QShortcut(QKeySequence("Del"), current_view)
        self.delete_shortcut.activated.connect(lambda: self.trash_item(set(self.model.filePath(index) for index in current_view.selectedIndexes())))

        self.new_file_shortcut = QShortcut(QKeySequence("Ctrl+N"), current_view)
        self.new_file_shortcut.activated.connect(self.create_new_file)

        self.new_folder_shortcut = QShortcut(QKeySequence("Ctrl+Shift+N"), current_view)
        self.new_folder_shortcut.activated.connect(self.create_new_folder)

        self.access_shortcut = QShortcut(QKeySequence("Ctrl+Shift+A"), current_view)
        self.access_shortcut.activated.connect(self.change_access)
        
        self.undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), current_view)
        self.undo_shortcut.activated.connect(self.undo_operation)
        
        self.open_shortcut = QShortcut(QKeySequence("Return"), current_view)
        self.open_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        self.open_shortcut.activated.connect(self.open_item)
        
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+F"), current_view)
        self.search_shortcut.activated.connect(self.search_bar.setFocus)
        
        self.parent_directory_shortcut = QShortcut(QKeySequence("Backspace"), current_view)
        self.parent_directory_shortcut.activated.connect(self.go_up)
        
        self.properties_shortcut = QShortcut(QKeySequence("Alt+Enter"), current_view)
        self.properties_shortcut.activated.connect(self.show_properties)

        self.add_to_favorites_shortcut = QShortcut(QKeySequence("Ctrl+B"), current_view)
        self.add_to_favorites_shortcut.activated.connect(lambda: self.pin_to_sidebar(self.model.filePath(current_view.currentIndex())))

        self.open_settings_shortcut = QShortcut(QKeySequence("Ctrl+Shift+I"), current_view)
        self.open_settings_shortcut.activated.connect(self.open_settings)
        
        self.save_tabs_shortcut = QShortcut(QKeySequence("Ctrl+S"), current_view)
        self.save_tabs_shortcut.activated.connect(self.save_tabs)

        self.new_tab_shortcut = QShortcut(QKeySequence("Ctrl+T"), current_view)
        self.new_tab_shortcut.activated.connect(self.add_new_tab)

    def add_new_tab(self, label: str=None, file_path: str=None):
        self.tab_iterator = self.tab_widget.count()
        if self.tab_widget.count() > 0:
            self.tab_iterator += 1
            if label is None:
                label = f"Tab {self.tab_iterator}"
        else:
            label = "Main"
        new_view = self.create_new_view(root_path=file_path) if label != "Main" else self.create_new_view(main_view=True)
        self.browser_history[label] = [file_path if label != "Main" else DESKTOP_PATH]
        self.browser_forward_history[label] = []
        if label != "Main":
            self.active_shortcuts(current_view=new_view)
            header = new_view.header()
            if IS_DARK:
                header.setStyleSheet(
                    "QHeaderView::section { background-color: #202020; color: #F0F0F0; border: none; }"
                    "QHeaderView::section:hover { background-color: #404040; }"
                    "QHeaderView::section:pressed { background-color: #606060; }"
                )
            else:
                header.setStyleSheet(
                    "QHeaderView::section { background-color: #FAFAFA; color: #333; border: none; }"
                    "QHeaderView::section:hover { background-color: #E1EFFB; }"
                    "QHeaderView::section:pressed { background-color: #DDD; }"
                )
        index = self.tab_widget.addTab(new_view, label)
        if label == "Main":
            self.make_tab_unclosable(index)

    def apply_theme_stylesheet(self):
        qa_header = self.quick_access_list.header()
        lv_header = self.main_view.header()
        sr_header = self.search_results_tree.header()
        if IS_DARK:
            self.setStyleSheet(
                "QTreeView { background-color: #202020; color: #F0F0F0; }"
                "QTreeView::item:selected { color: #F0F0F0; background-color: #1A364D; }"
                "QTreeView::branch:closed:has-children:has-siblings, QTreeView::branch:closed:has-children:!has-siblings { image:url(icons/branch-closed.png) }"
                "QTreeView::branch:open:has-children:has-siblings, QTreeView::branch:open:has-children:!has-siblings { image:url(icons/branch-open.png) }"
                "QTreeView::branch:closed:hover:has-children:has-siblings, QTreeView::branch:closed:hover:has-children:!has-siblings { image:url(icons/branch-closed-hover.png) }"
                "QTreeView::branch:open:hover:has-children:has-siblings, QTreeView::branch:open:hover:has-children:!has-siblings { image:url(icons/branch-open-hover.png) }"
                "QDockWidget { background-color: #202020; color: #F0F0F0; }"
                "QMainWindow { background-color: #2D2D2D; }"
                "CustomTitleBar { background-color: #2D2D2D; color: #F0F0F0; border-bottom: 1px solid #404040; }"
                "#CloseButton { color: #F0F0F0; background-color: #2D2D2D; border: none; }"
                "#CloseButton:hover { background-color: #E81123; }"
                "#MaximizeButton { color: #F0F0F0; background-color: #2D2D2D; border: none; }"
                "#MaximizeButton:hover { background-color: #283642; }"
                "#MinimizeButton { color: #F0F0F0; background-color: #2D2D2D; border: none; }"
                "#MinimizeButton:hover { background-color: #283642; }"
                "#SettingsButton { color: #F0F0F0; background-color: #2D2D2D; border: none; }"
                "#SettingsButton:hover { background-color: #283642; }"
                "QToolBar { background-color: transparent; border: none; spacing: 5px; }"
                "QToolButton { color: #F0F0F0; font-size: 10pt; font-weight: bold; padding: 0px; border: none; border-radius: 5px; }"
                "QToolButton:hover { background-color: #283642; }"
                "#OpenSidebarButton { background-color: #202020; color: #F0F0F0;  font-size: 8.5pt; }"
                "#SearchModeButton { background-color: #202020; color: #F0F0F0;  font-size: 8.5pt; border-radius: 5px; }"
                "#SearchModeButton:hover { background-color: #283642; }"
                "#FileCountLabel { color: #F0F0F0;  font-size: 8.5pt; padding-right: 10px; }"
                "#IndexLabel { color: #F0F0F0;  font-size: 8.5pt; padding-right: 10px; }"
                "#PreviewWindow { color: #F0F0F0;  font-size: 8.5pt; padding-right: 10px; }"
                "QStatusBar { background-color: transparent; border-bottom: 1px solid #404040; }"
                "#AccessButton { background-color: transparent; color: #F0F0F0;  font-size: 8.5pt; border: none; border-radius: 5px; }"
                "#AccessButton:hover { background-color: #283642; }"
                "#StatusLabel { color: #F0F0F0;  font-size: 8.5pt; padding-right: 10px; }"
                "#SearchInfoLabel { color: #F0F0F0; font-size: 8.5pt; }"
                "QSplitter::handle { background-color: #2D2D2D; }"
                "QScrollBar:vertical { border: none; background-color: #202020; width: 8px; margin: 0px; }"
                "QScrollBar:horizontal { border: none; background-color: #202020; height: 8px; margin: 0px; }"
                "QScrollBar:vertical:hover { width: 15px; }"
                "QScrollBar:horizontal:hover { height: 15px; }"
                "QScrollBar::handle:vertical { background-color: #606060; min-height: 20px; }"
                "QScrollBar::handle:horizontal { background-color: #606060; min-width: 20px; }"
                "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,"
                "QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { border: none; background-color: none; height: 0px; width: 0px; }"
                "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,"
                "QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background-color: none; }"
                "QComboBox { background-color: #202020; color: #F0F0F0; font-size: 8.5pt; border-top: 1px solid #404040; border-left: 1px solid #404040; border-right: 1px solid #404040; }"
                "QComboBox:hover { background-color: #283642; }"
                "QComboBox:focus { background-color: #303030; }"
                "QComboBox:disabled { background-color: #202020; color: #808080; border: 1px solid #404040; }"
                "QComboBox QAbstractItemView { background-color: #202020; color: #F0F0F0; selection-background-color: #303030; selection-color: #F0F0F0; border: 1px solid #404040; }"
                "QMenu { background-color: #202020; color: #F0F0F0; border: 1px solid #404040; }"
                "QMenu::item:selected { background-color: #283642; }"
                "QProgressBar { background-color: #202020; border-radius: 4px; border-bottom: 1px solid #404040; border-left: 1px solid #404040; border-right: 1px solid #404040; }"
                "QProgressBar::chunk { background-color: #0078D4; border-radius: 2px; }"
                "QProgressBar[completed='true']::chunk { background-color: #65C64F; }"
                "QWidget#PropertiesWindow { background-color: #202020; color: #F0F0F0; }"
                "QLineEdit#PropertiesLineEdit { background-color: #202020; color: #F0F0F0; border: none; }"
                "QLineEdit#PropertiesLineEdit:hover { background-color: #283642; }"
                "QLineEdit#PropertiesLineEdit:focus { background-color: #303030; }"
                "QFormLayout#PropertiesFormLayout { margin: 10px; }"
                "#PropertiesLabel { color: #F0F0F0; }"
                "#AddressBarEdit { background-color: #202020; color: #F0F0F0; font-size: 8.5pt; border: 1px solid #404040; }"
                "#AddressBarEdit:focus { background-color: #303030; }"
                "BreadcrumbsBar QPushButton { background-color: transparent; color: #F0F0F0; padding: 5px; font-size: 8.5pt; border: none; }"
                "BreadcrumbsBar QPushButton:hover { background-color: #283642; color: #F0F0F0; }"
                "BreadcrumbsBar QWidget#breadcrumb_widget { background-color: #202020; border: 1px solid #404040; }"
                "#CustomTabWidget::pane { border: 1px solid #404040; background-color: #202020; } "
                "#MainTabBar::tab { background-color: #202020; color: #F0F0F0; border: 1px solid #404040; padding-top: 3px; padding-bottom: 3px; padding-left: 15px; padding-right: 15px; margin-right: 2px; } "
                "#MainTabBar::tab:selected { background-color: #2D2D2D; color: #FFFFFF; border-bottom-color: #2D2D2D; } "
                "#MainTabBar::tab:!selected { background-color: #202020; color: #F0F0F0; } "
                "#MainTabBar::tab:hover { background-color: #283642; border-color: #283642; } "
                "#NewTabButton { background-color: #202020; color: #F0F0F0;  font-size: 10pt; border: none; border-radius: 2px; }"
                "#NewTabButton:hover { background-color: #283642; }"
                "#DetailsBar { background-color: #202020; color: #F0F0F0; padding-left: 5px; border: 1px solid #404040; }"
            )
            self.title_bar.setStyleSheet(
                "#TitleLabel { color: #F0F0F0; font-size: 9pt; font-weight: bold; padding: 5px; }"
                "#SettingsButton { background-color: transparent; color: #F0F0F0;  font-size: 8.5pt; }"
                "#SettingsButton:hover { background-color: #283642; }"
                )
            qa_header.setStyleSheet(
                "QHeaderView::section { background-color: #202020; color: #F0F0F0; border: 1px solid #D3D3D3; }"
                "QHeaderView::section:hover { background-color: #404040; }"
                "QHeaderView::section:pressed { background-color: #606060; }"
                )
            lv_header.setStyleSheet(
                "QHeaderView::section { background-color: #202020; color: #F0F0F0; border: none; }"
                "QHeaderView::section:hover { background-color: #404040; }"
                "QHeaderView::section:pressed { background-color: #606060; }"
                )
            sr_header.setStyleSheet(
                "QHeaderView::section { background-color: #202020; color: #F0F0F0; border: none; padding: 10px; }"
                "QHeaderView::section:hover { background-color: #404040; }"
                "QHeaderView::section:pressed { background-color: #606060; }"
                )
        else:
            self.setStyleSheet(
                "QTreeView { background-color: #FAFAFA; color: #333; }"
                "QTreeView::item:selected { color: #333; background-color: #CCE8FF; }"
                "QTreeView::branch:closed:has-children:has-siblings, QTreeView::branch:closed:has-children:!has-siblings { image:url(icons/branch-closed.png) }"
                "QTreeView::branch:open:has-children:has-siblings, QTreeView::branch:open:has-children:!has-siblings { image:url(icons/branch-open.png) }"
                "QTreeView::branch:closed:hover:has-children:has-siblings, QTreeView::branch:closed:hover:has-children:!has-siblings { image:url(icons/branch-closed-hover.png) }"
                "QTreeView::branch:open:hover:has-children:has-siblings, QTreeView::branch:open:hover:has-children:!has-siblings { image:url(icons/branch-open-hover.png) }"
                "QDockWidget { background-color: #EFEFEF; color: #333; }"
                "QMainWindow { background-color: #F5F5F5; }"
                "CustomTitleBar { background-color: #F5F5F5; color: #333; border-bottom: 1px solid #D9D9D9; }"
                "#CloseButton { color: #333; background-color: #F5F5F5; border: none; }"
                "#CloseButton:hover { color: #F0F0F0; background-color: #E81123; }"
                "#MaximizeButton { color: #333; background-color: #F5F5F5; border: none; }"
                "#MaximizeButton:hover { background-color: #E1EFFB; }"
                "#MinimizeButton { color: #333; background-color: #F5F5F5; border: none; }"
                "#MinimizeButton:hover { background-color: #E1EFFB; }"
                "#SettingsButton { color: #333; background-color: #F5F5F5; border: none; }"
                "#SettingsButton:hover { background-color: #E1EFFB; }"
                "QToolBar { background-color: transparent; border: none; spacing: 5px; }"
                "QToolButton { color: #333; background-color: #F5F5F5; font-size: 10pt; font-weight: bold; padding: 0px; border: none; border-radius: 5px; }"
                "QToolButton:hover { background-color: #E1EFFB; }"
                "#OpenSidebarButton { background-color: #EFEFEF; color: #333; font-size: 8.5pt; }"
                "#SearchModeButton { background-color: #D9D9D9; color: #333; font-size: 8.5pt; border: none; border-radius: 5px; }"
                "#SearchModeButton:hover { background-color: #E1EFFB; }"
                "#FileCountLabel, #IndexLabel, #PreviewLabel, #StatusLabel, #SearchInfoLabel { color: #333; font-size: 8.5pt; padding-right: 10px; }"
                "QStatusBar { background-color: transparent; border-bottom: 1px solid #D9D9D9; }"
                "#AccessButton { background-color: transparent; color: #333; font-size: 8.5pt; border: none; border-radius: 5px; }"
                "#AccessButton:hover { background-color: #E1EFFB; }"
                "QSplitter::handle { background-color: #EDEDED; }"
                "QScrollBar:vertical { border: none; background-color: #F5F5F5; width: 8px; margin: 0px; }"
                "QScrollBar:horizontal { border: none; background-color: #F5F5F5; height: 8px; margin: 0px; }"
                "QScrollBar:vertical:hover { width: 15px; }"
                "QScrollBar:horizontal:hover { height: 15px; }"
                "QScrollBar::handle:vertical { background-color: #D9D9D9; min-height: 20px; }"
                "QScrollBar::handle:horizontal { background-color: #D9D9D9; min-width: 20px; }"
                "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,"
                "QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { border: none; background-color: none; height: 0px; width: 0px; }"
                "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,"
                "QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background-color: none; }"
                "QComboBox { background-color: #FFFFFF; color: #333; font-size: 8.5pt; border-top: 1px solid #D9D9D9; border-left: 1px solid #D9D9D9; border-right: 1px solid #D9D9D9; }"
                "QComboBox:hover { background-color: #E1EFFB; }"
                "QComboBox:focus { background-color: #E5E5E5; }"
                "QComboBox:disabled { background-color: #FAFAFA; color: #888; border: 1px solid #D9D9D9; }"
                "QComboBox QAbstractItemView { background-color: #FFFFFF; color: #333; selection-background-color: #E0E0E0; selection-color: #333; border: 1px solid #D9D9D9; }"
                "QMenu { background-color: #FAFAFA; color: #333; border: 1px solid #D9D9D9; }"
                "QMenu::item:selected { background-color: #E0E0E0; }"
                "QProgressBar { background-color: #EFEFEF; border-radius: 4px; border-bottom: 1px solid #D9D9D9; border-left: 1px solid #D9D9D9; border-right: 1px solid #D9D9D9; }"
                "QProgressBar::chunk { background-color: #3092C7; border-radius: 2px; }"
                "QProgressBar[completed='true']::chunk { background-color: #69B342; }"
                "QWidget#PropertiesWindow { background-color: #FAFAFA; color: #333; }"
                "QLineEdit#PropertiesLineEdit { background-color: #FFFFFF; color: #333; border: none; }"
                "QLineEdit#PropertiesLineEdit:hover { background-color: #E1EFFB; }"
                "QLineEdit#PropertiesLineEdit:focus { background-color: #E5E5E5; }"
                "QFormLayout#PropertiesFormLayout { margin: 10px; }"
                "#PropertiesLabel { color: #333; }"
                "#AddressBarEdit { background-color: #FFFFFF; color: #333; font-size: 8.5pt; border: 1px solid #D9D9D9; }"
                "#AddressBarEdit:focus { background-color: #E5E5E5; }"
                "BreadcrumbsBar QPushButton { background-color: transparent; color: #333; padding: 5px; font-size: 8.5pt; border: none; }"
                "BreadcrumbsBar QPushButton:hover { background-color: #E1EFFB; color: #333; }"
                "BreadcrumbsBar QWidget#breadcrumb_widget { background-color: #FFFFFF; border: 1px solid #D9D9D9; }"
                "#CustomTabWidget::pane { border: 1px solid #D9D9D9; }"
                "#MainTabBar::tab { background-color: #EFEFEF; color: #333; border: 1px solid #D9D9D9; padding-top: 3px; padding-bottom: 3px; padding-left: 15px; padding-right: 15px; margin-right: 2px; }"
                "#MainTabBar::tab:selected { background-color: #F5F5F5; color: #000000; }"
                "#MainTabBar::tab:!selected { background-color: #EFEFEF; color: #333; }"
                "#MainTabBar::tab:hover { background-color: #E1EFFB; }"
                "#MainTabBar::tab:selected { border-color: #D9D9D9; border-bottom-color: #F5F5F5; }"
                "#NewTabButton { background-color: #D9D9D9; color: #333; font-size: 10pt; border: none; border-radius: 2px; }"
                "#NewTabButton:hover { background-color: #E1EFFB; }"
                "#DetailsBar { background-color: #FAFAFA; color: #333; padding-left: 5px; border: 1px solid #D9D9D9; }"
            )
            self.title_bar.setStyleSheet(
                "#TitleLabel { color: #333; font-size: 9pt; font-weight: bold; padding: 5px; }"
                "#SettingsButton { background-color: transparent; color: #333;  font-size: 8.5pt; }"
                "#SettingsButton:hover { background-color: #E1EFFB; }"
                )
            qa_header.setStyleSheet(
                "QHeaderView::section { background-color: #FAFAFA; color: #333; border: 1px solid #AAA; }"
                "QHeaderView::section:hover { background-color: #E1EFFB; }"
                "QHeaderView::section:pressed { background-color: #DDD; }"
                )
            lv_header.setStyleSheet(
                "QHeaderView::section { background-color: #FAFAFA; color: #333; border: none; }"
                "QHeaderView::section:hover { background-color: #E1EFFB; }"
                "QHeaderView::section:pressed { background-color: #DDD; }"
                )
            sr_header.setStyleSheet(
                "QHeaderView::section { background-color: #FAFAFA; color: #333; border: none; padding: 10px; }"
                "QHeaderView::section:hover { background-color: #E1EFFB; }"
                "QHeaderView::section:pressed { background-color: #DDD; }"
                )

    def browse_folder(self, file_path: str, browse: bool=False, browse_to: bool=False, new_tab: bool=False):
        if new_tab:
            if browse:
                new_tab_path = file_path if path.isdir(file_path) else path.dirname(file_path)
            else:
                new_tab_path = path.dirname(file_path)
            self.add_new_tab(label=path.basename(new_tab_path), file_path=new_tab_path)
            self.tab_widget.setCurrentIndex(self.tab_widget.count()-1)
        else:
            self.get_current_view().setRootIndex(self.model.index(file_path if path.isdir(file_path) else path.dirname(file_path)))
        self.update_address_bar()
        tab_name = self.tab_widget.tabText(self.tab_widget.currentIndex())
        self.browser_history[tab_name].append(self.current_path)
        self.browser_forward_history[tab_name] = []
        if browse_to:
            current_view = self.get_current_view()
            index = self.model.index(file_path)
            current_view.scrollTo(index)
            current_view.selectionModel().select(index, QItemSelectionModel.SelectionFlag.ClearAndSelect)

    def change_access(self):
        if self.access.text() == "Read":
            self.access.setText("Write")
        else:
            self.access.setText("Read")

    def change_search_mode(self):
        current_mode = self.search_bar.placeholderText()
        if "All Drives" in current_mode:
            self.search_mode_button.setIcon(QIcon(path.join(ICONS_PATH, "w_current_path.png") if IS_DARK is True else path.join(ICONS_PATH, "b_current_path.png")))
            self.search_bar.setPlaceholderText("Search Current Path")
        elif "Current Path" in current_mode:
            self.search_mode_button.setIcon(QIcon(path.join(ICONS_PATH, "w_all_drives.png") if IS_DARK is True else path.join(ICONS_PATH, "b_all_drives.png")))
            self.search_bar.setPlaceholderText("Search All Drives")
        self.search_mode_button.setToolTip(self.search_bar.placeholderText())

    def cleanup(self):
        self.close()
        self.status_checker.terminate()
        self.indexer.stop()
        self.save_tabs()
        if path.exists(path.join(INDEXES_PATH, f"{COMPUTERNAME}_is_alive")):
            remove(path.join(INDEXES_PATH, f"{COMPUTERNAME}_is_alive"))
        self.purge_temp_folder()

    def close_tab(self, index):
        widget_to_remove = self.tab_widget.widget(index)
        if widget_to_remove is not None:
            widget_to_remove.deleteLater()
        self.tab_widget.removeTab(index)

    def compress_items(self, file_paths: list):
        import zipfile
        zip_path = file_paths[0].split(".")[0] + ".zip" if len(file_paths) == 1 else path.join(self.current_path, "compressed_items.zip")
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
            for file_path in file_paths:
                if path.isdir(file_path):
                    for dirpath, dirnames, filenames in walk(file_path):
                        for filename in filenames:
                            relative_path = path.relpath(path.join(dirpath, filename), file_path)
                            zipf.write(path.join(dirpath, filename), arcname=relative_path)
                else:
                    zipf.write(file_path, arcname=path.basename(file_path))
        self.undo_history.append(("compress", zip_path))

    def copy_item(self, file_paths: list, copy_type: str):
        mime_data = QMimeData()
        if copy_type == "item":
            mime_data.setUrls([QUrl.fromLocalFile(file_path) for file_path in file_paths])
        elif copy_type == "name":
            name = path.basename(file_paths[0])
            mime_data.setText(name)
        elif copy_type == "basename":
            name, _ = path.splitext(path.basename(file_paths[0]))
            mime_data.setText(name)
        elif copy_type == "path":
            copied_path = path.normpath(file_paths[0])
            name = path.basename(copied_path)
            self.copied_path_item = (name, copied_path)
            mime_data.setText(copied_path)
        elif copy_type == "current path":
            mime_data.setText(self.current_path)
        self.clipboard.setMimeData(mime_data)

    def create_context_menu(self, point: QPoint):
        context_menu = QMenu(self)
        current_view = self.get_current_view()
        if self.sender() == current_view:
            indices = current_view.selectedIndexes()
            unique_paths = set()
            file_paths = []
            for index in indices:
                file_path = self.model.filePath(index)
                if file_path not in unique_paths:
                    unique_paths.add(file_path)
                    file_paths.append(file_path)
            # File/Folder operations
            if len(file_paths) == 1:
                if path.isdir(file_paths[0]):
                    browse_action = QAction("Browse", context_menu)
                    browse_action.triggered.connect(lambda: self.browse_folder(file_paths[0]))
                    context_menu.addAction(browse_action)
                    browse_new_tab_action = QAction("Browse in New Tab", context_menu)
                    browse_new_tab_action.triggered.connect(lambda: self.browse_folder(path, browse=True, new_tab=True))
                    context_menu.addAction(browse_new_tab_action)
                else:
                    open_action = QAction("Open", context_menu)
                    open_action.triggered.connect(lambda: startfile(file_paths[0]))
                    context_menu.addAction(open_action)
                    browse_to_new_tab_action = QAction("Browse to in New Tab", context_menu)
                    browse_to_new_tab_action.triggered.connect(lambda: self.browse_folder(path, browse_to=True, new_tab=True))
                    context_menu.addAction(browse_to_new_tab_action)

                rename_action = QAction("Rename", context_menu)
                rename_action.triggered.connect(lambda: self.rename_item(file_paths[0]))
                context_menu.addAction(rename_action)
            
            if len(file_paths) >= 1:
                delete_action = QAction("Delete All" if len(file_paths) > 1 else "Delete", context_menu)
                delete_action.triggered.connect(lambda: self.trash_item(file_paths))
                context_menu.addAction(delete_action)

                move_action = QAction("Move All..." if len(file_paths) > 1 else "Move...", context_menu)
                move_action.triggered.connect(lambda: self.move_item(file_paths))
                context_menu.addAction(move_action)
                
                copy_action = QAction("Copy All" if len(file_paths) > 1 else "Copy", context_menu)
                copy_action.triggered.connect(lambda: self.copy_item(file_paths, "item"))
                context_menu.addAction(copy_action)
            
            # Other copy operations
            if len(file_paths) == 1:
                copy_submenu = QMenu("More Copy Options...", context_menu)

                copy_name_action = QAction("Copy Name", copy_submenu)
                copy_name_action.triggered.connect(lambda: self.copy_item(file_paths, "name"))
                copy_submenu.addAction(copy_name_action)
                
                copy_basename_action = QAction("Copy Basename", copy_submenu)
                copy_basename_action.triggered.connect(lambda: self.copy_item(file_paths, "basename"))
                copy_submenu.addAction(copy_basename_action)

                copy_path_action = QAction("Copy Path", copy_submenu)
                copy_path_action.triggered.connect(lambda: self.copy_item(file_paths, "path"))
                copy_submenu.addAction(copy_path_action)

                copy_current_path_action = QAction("Copy Parent Path", copy_submenu)
                copy_current_path_action.triggered.connect(lambda: self.copy_item(file_paths, "current path"))
                copy_submenu.addAction(copy_current_path_action)

                context_menu.addMenu(copy_submenu)

            # Compress and Extract operations
            if len(file_paths) == 1:
                if path.splitext(file_paths[0])[1].lower() != ".zip":
                    compress_action = QAction("Compress", context_menu)
                    compress_action.triggered.connect(lambda: self.compress_items(file_paths))
                    context_menu.addAction(compress_action)
                else:
                    extract_action = QAction("Extract", context_menu)
                    extract_action.triggered.connect(lambda: self.extract_item(file_paths[0]))
                    context_menu.addAction(extract_action)

            elif len(file_paths) > 1:
                if not any([path.splitext(file_path)[1].lower() == ".zip" for file_path in file_paths]):
                    compress_action = QAction("Compress All", context_menu)
                    compress_action.triggered.connect(lambda: self.compress_items(file_paths))
                    context_menu.addAction(compress_action)
            
            # Clipboard operations
            if len(self.clipboard.mimeData().formats()) > 0 and len(self.copied_path_item) == 0:
                context_menu.addSeparator()
                paste_action = QAction("Paste", context_menu)
                paste_action.triggered.connect(self.paste_item)
                context_menu.addAction(paste_action)
                
            elif len(self.clipboard.mimeData().formats()) > 0 and len(self.copied_path_item) > 0:
                context_menu.addSeparator()
                paste_search_shortcut_action = QAction(f"Paste Shortcut [{self.copied_path_item[0]}]", context_menu)
                paste_search_shortcut_action.triggered.connect(lambda: self.create_shortcut(self.copied_path_item[1], dest_path=self.current_path))
                context_menu.addAction(paste_search_shortcut_action)
            

            # Special operations
            context_menu.addSeparator()
            if len(file_paths) == 1:
                create_shortcut_action = QAction("Create Shortcut", context_menu)
                create_shortcut_action.triggered.connect(lambda: self.create_shortcut(file_paths[0]))
                context_menu.addAction(create_shortcut_action)
                
                pin_action = QAction("Pin to Sidebar", context_menu)
                pin_action.triggered.connect(lambda: self.pin_to_sidebar(file_paths[0]))
                context_menu.addAction(pin_action)
                
                properties_action = QAction("Properties", context_menu)
                properties_action.triggered.connect(lambda: self.show_properties(file_paths[0]))
                context_menu.addAction(properties_action)
                
                duplicate_tab_action = QAction("Duplicate Tab", context_menu)
                duplicate_tab_action.triggered.connect(lambda: self.browse_folder(path, new_tab=True))
                context_menu.addAction(duplicate_tab_action)
            
            # PDF operations
            if len(file_paths) == 2 and path.splitext(file_paths[0])[1].lower() == ".pdf":
                context_menu.addSeparator()
                compare_pdfs_action = QAction("Compare", context_menu)
                compare_pdfs_action.triggered.connect(self.start_comparing)
                context_menu.addAction(compare_pdfs_action)
            
            # Creation operations
            context_menu.addSeparator()
            new_file_action = QAction("New File", context_menu)
            new_file_action.triggered.connect(self.create_new_file)
            context_menu.addAction(new_file_action)

            new_folder_action = QAction("New Folder", context_menu)
            new_folder_action.triggered.connect(self.create_new_folder)
            context_menu.addAction(new_folder_action)
            
            if len(file_paths) >= 1:
                context_menu.addSeparator()
                power_rename_action = QAction("Power Rename", context_menu)
                power_rename_action.triggered.connect(lambda: self.power_rename(file_paths))
                context_menu.addAction(power_rename_action)

                whats_using_action = QAction("What's using this file", context_menu)
                whats_using_action.triggered.connect(lambda: self.show_whats_using_file(file_paths[0]))
                context_menu.addAction(whats_using_action)
        
        # Pinned operations
        elif self.sender() == self.pinned:
            item = self.pinned.itemAt(point)
            if item:
                remove_pin_action = QAction("Remove", context_menu)
                remove_pin_action.triggered.connect(lambda: self.remove_pinned_item(item))
                context_menu.addAction(remove_pin_action)
                
                rename_pin_action = QAction("Rename", context_menu)
                rename_pin_action.triggered.connect(lambda: self.rename_pinned_item(item))
                context_menu.addAction(rename_pin_action)
                
                relink_action = QAction("Relink", context_menu)
                relink_action.triggered.connect(lambda: self.relink_pinned_item(item))
                context_menu.addAction(relink_action)
        
        # Search results operations
        elif self.sender() == self.search_results_tree:
            item = self.search_results_tree.itemAt(point)
            if item:
                file_path = item.data(0, Qt.ItemDataRole.UserRole)
            
                if path.isdir(file_path):
                    results_browse_action = QAction("Browse", context_menu)
                    results_browse_action.triggered.connect(lambda: self.browse_folder(file_path))
                                
                else:
                    open_action = QAction("Open", context_menu)
                    open_action.triggered.connect(lambda: startfile(file_path))
                    
                results_browse_to_action = QAction("Browse to", context_menu)
                results_browse_to_action.triggered.connect(lambda: self.browse_folder(file_path, browse_to=True))
                context_menu.addAction(results_browse_to_action)
            
                results_browse_new_tab_action = QAction("Browse to in New Tab", context_menu)
                results_browse_new_tab_action.triggered.connect(lambda: self.browse_folder(file_path, browse_to=True, new_tab=True))
                context_menu.addAction(results_browse_new_tab_action)
                
                copy_path_action = QAction("Copy Path", context_menu)
                copy_path_action.triggered.connect(lambda: self.copy_item([file_path], "path"))
                context_menu.addAction(copy_path_action)
        else:
            print(self.sender())
        
        context_menu.exec_(self.sender().mapToGlobal(point))

    def create_new_file(self):
        if self.access.text() == "Write":
            file_name, _ = QInputDialog.getText(self, "New File", "Enter the name of the new file:")
            if file_name:
                for char in ["/", "\\", ":", "*", "?", '"', "|", "<", ">"]:
                    if char in file_name:
                        QMessageBox.information(self, "File Name Error", "File names cannot contain: / \\ : * ? | < >")
                with open(path.join(self.current_path, file_name), "w") as f:
                    f.write("")
                self.update_file_count()
                self.undo_history.append(("new-file", path.join(self.current_path, file_name)))
        else:
            QMessageBox.information(self, "Permission Error", "You dont have the required permissions.")

    def create_new_folder(self):
        if self.access.text() == "Write":
            folder_name, _ = QInputDialog.getText(self, "New Folder", "Enter the name of the new folder:")
            if folder_name:
                for char in ["/", "\\", ":", "*", "?", '"', "|", "<", ">"]:
                    if char in folder_name:
                        QMessageBox.information(self, "File Name Error", "File names cannot contain: / \\ : * ? | < >")
                makedirs(path.join(self.current_path, folder_name))
                self.update_file_count()
                self.undo_history.append(("new-folder", path.join(self.current_path, folder_name)))
        else:
            QMessageBox.information(self, "Permission Error", "You don't have the required permissions.")

    def create_new_view(self, main_view: bool=False, root_path: str=None) -> TreeView:
        if main_view:
            if self.load_general_settings().get("RELOAD_MAIN_TAB"):
                try:
                    with open(path.join(SETTINGS_PATH, f"{COMPUTERNAME}_tabs.json"), "r") as file:
                        tabs = load(file)
                        self.main_view.setRootIndex(self.model.index(tabs["Main"]))
                        return self.main_view
                except FileNotFoundError:
                    return main_view
            else:
                return self.main_view
        new_view = TreeView(self)
        new_view.setModel(self.model)
        if not root_path:
            new_view.setRootIndex(self.model.index(DESKTOP_PATH))
        else:
            new_view.setRootIndex(self.model.index(root_path))
        new_view.header().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        new_view.setColumnWidth(0, 400)
        new_view.setSortingEnabled(True)
        new_view.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        new_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        new_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        new_view.setUniformRowHeights(True)
        new_view.setDragEnabled(True)
        new_view.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        new_view.dropAccepted.connect(self.handle_drop)

        new_view.clicked.connect(self.on_item_clicked)
        new_view.doubleClicked.connect(self.on_item_double_clicked)

        new_view.selectionModel().selectionChanged.connect(self.update_address_bar)
        new_view.selectionModel().selectionChanged.connect(self.preview.update_preview)

        new_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        new_view.customContextMenuRequested.connect(self.create_context_menu)

        return new_view

    def create_shortcut(self, source_path: str, dest_path: str=None):
        shell_link = CoCreateInstance(
            shell.CLSID_ShellLink, 
            None,
            CLSCTX_INPROC_SERVER, 
            shell.IID_IShellLink
        )
        shell_link.SetPath(source_path)
        name, ext = path.splitext(path.basename(source_path))
        if dest_path is None:
            desktop_path = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, None, 0)
            dest_path = path.join(desktop_path, f"{name} - Shortcut.lnk")
        else:
            self.copied_search_result = ()
            dest_path = path.join(dest_path, f"{name} - Shortcut.lnk")
        persist_file = shell_link.QueryInterface(IID_IPersistFile)
        persist_file.Save(dest_path, 0)
        self.undo_history.append(("new-shortcut", dest_path))

    def extract_item(self, zip_path: str):
        extract_folder = path.splitext(zip_path)[0]
        with ZipFile(zip_path, "r") as zipf:
            zipf.extractall(extract_folder)
        self.undo_history.append(("extract", extract_folder))

    def format_file_size(self, size_in_bytes: int) -> str:
        suffixes = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
        if size_in_bytes == 0:
            return ""
        i = 0
        while size_in_bytes >= 1000 and i < len(suffixes)-1:
            size_in_bytes /= 1000.0
            i += 1
        return f"{size_in_bytes:.2f} {suffixes[i]}"

    def get_current_view(self) -> TreeView:
        return self.tab_widget.currentWidget()
    
    def get_directory_contents(self, start_path: str) -> tuple:
        num_files = 0
        num_dirs = 0
        for dirpath, dirnames, filenames in walk(start_path):
            num_files += len(filenames)
            num_dirs += len(dirnames)
        return num_files, num_dirs

    def get_directory_size(self, start_path: str) -> float:
        total_size = 0
        for dirpath, dirnames, filenames in walk(start_path):
            for f in filenames:
                fp = path.join(dirpath, f)
                try:
                    total_size += path.getsize(fp)
                except:
                    pass
        return total_size

    def get_file_owner(self, file_path: str) -> str:
        sd = GetFileSecurity(file_path, OWNER_SECURITY_INFORMATION)
        owner_sid = sd.GetSecurityDescriptorOwner()
        try:
            owner_name, domain, _ = LookupAccountSid(None, owner_sid)
        except:
            owner_name, domain = "Error", None
        return owner_name
    
    def get_items_from_tree(self, tree, parent_item=None):
        items = []
        child_count = tree.topLevelItemCount() if parent_item is None else parent_item.childCount()
        for i in range(child_count):
            item = tree.topLevelItem(i) if parent_item is None else parent_item.child(i)
            name = item.text(0)
            file_path = item.data(0, Qt.ItemDataRole.UserRole)
            children = self.get_items_from_tree(tree, item)
            items.append({"name": name, "path": file_path, "children": children})
        return items

    def get_mounted_drives(self) -> list:
        drives = GetLogicalDriveStrings()
        drives = drives.split("\000")[:-1]
        return [drive[0] for drive in drives]

    def go_back(self):
        tab_name = self.tab_widget.tabText(self.tab_widget.currentIndex())
        if len(self.browser_history[tab_name]) > 1:
            self.browser_forward_history[tab_name].append(self.browser_history[tab_name].pop())
            current_path = self.browser_history[self.tab_widget.tabText(self.tab_widget.currentIndex())][-1]
            current_view = self.get_current_view()
            current_view.setRootIndex(self.model.index(current_path))
            self.update_address_bar()

    def go_forward(self):
        tab_name = self.tab_widget.tabText(self.tab_widget.currentIndex())
        if self.browser_forward_history[tab_name]:
            current_path = self.browser_forward_history[tab_name].pop()
            self.browser_history[tab_name].append(self.current_path)
            current_view = self.get_current_view()
            current_view.setRootIndex(self.model.index(current_path))
            self.update_address_bar()

    def go_up(self):
        tab_name = self.tab_widget.tabText(self.tab_widget.currentIndex())
        current_path = "\\".join(self.address_bar.text().split("\\")[:-1])
        self.browser_history[tab_name].append(self.current_path)
        current_view = self.get_current_view()
        current_view.setRootIndex(self.model.index(current_path))
        self.update_address_bar()

    def handle_drop(self, paths: list, is_internal: bool):
        current_view = self.get_current_view()
        destination_index = current_view.indexAt(current_view.viewport().mapFromGlobal(QCursor.pos()))
        if destination_index.isValid() and self.model.isDir(destination_index):
            destination_path = self.model.filePath(destination_index)
        else:
            destination_path = self.current_path
        
        if is_internal:
            self.move_item(paths, destination_path)
        else:
            if self.load_general_settings().get("EXTERNAL_DROP_MODE") == "Paste":
                self.paste_paths(paths)
            else:
                self.move_item(paths, destination_path)

    def handle_single_click(self, index: int):
        if QTimer().remainingTime() - self.last_clicked_timestamp > 0:
            current_view = self.get_current_view()
            current_view.selectionModel().clearSelection()
            current_view.selectionModel().select(index, QItemSelectionModel.SelectionFlag.Select)
            self.preview.update_preview()
    
    def is_near_edge(self, cursor_pos, screenGeometry, edge):
        threshold = 15
        if edge == "top_left":
            return self.is_near_edge(cursor_pos, screenGeometry, "top") and \
                self.is_near_edge(cursor_pos, screenGeometry, "left")
        elif edge == "top_right":
            return self.is_near_edge(cursor_pos, screenGeometry, "top") and \
                self.is_near_edge(cursor_pos, screenGeometry, "right")
        elif edge == "bottom_left":
            return self.is_near_edge(cursor_pos, screenGeometry, "bottom") and \
                self.is_near_edge(cursor_pos, screenGeometry, "left")
        elif edge == "bottom_right":
            return self.is_near_edge(cursor_pos, screenGeometry, "bottom") and \
                self.is_near_edge(cursor_pos, screenGeometry, "right")
        elif edge == "left":
            return abs(cursor_pos.x() - screenGeometry.left()) < threshold
        elif edge == "right":
            return abs(cursor_pos.x() - screenGeometry.right()) < threshold
        elif edge == "top":
            return abs(cursor_pos.y() - screenGeometry.top()) < threshold
        elif edge == "bottom":
            return abs(cursor_pos.y() - screenGeometry.bottom()) < threshold+ 40

    def is_network_drive(self, drive: str) -> bool:
        drive_type = GetDriveType(f"{drive}:\\")
        return drive_type == DRIVE_REMOTE
    
    def load_items_to_tree(self, items, parent_item=None):
        for item_data in items:
            item = QTreeWidgetItem([item_data["name"]])
            item.setData(0, Qt.ItemDataRole.UserRole, item_data["path"])
            if parent_item:
                parent_item.addChild(item)
            else:
                self.pinned.addTopLevelItem(item)
            self.load_items_to_tree(item_data["children"], item)

    def load_pinned_items(self):
        file_path = path.join(SETTINGS_PATH, f"{COMPUTERNAME}_pinned-items.json")
        if path.exists(file_path):
            with open(file_path, "r") as f:
                items = load(f)
        
            self.pinned.blockSignals(True)
            self.pinned.clear()
            self.load_items_to_tree(items)
            self.pinned.blockSignals(False)
            
    def load_general_settings(self) -> dict:
        general_settings_path = path.join(SETTINGS_PATH, f"{COMPUTERNAME}_general-settings.json")
        default_settings = {
            "SCROLL_TO": False,
            "REPLACE_DUPLICATES": False,
            "EXTERNAL_DROP_MODE": "Paste"
        }

        if path.exists(general_settings_path):
            with open(general_settings_path, "r") as f:
                general_settings = load(f)
            updated = False
            for key, value in default_settings.items():
                if key not in general_settings:
                    general_settings[key] = value
                    updated = True

            if updated:
                with open(general_settings_path, "w") as f:
                    dump(general_settings, f, indent=4)
        else:
            general_settings = default_settings
            with open(general_settings_path, "w") as f:
                dump(general_settings, f, indent=4)

        return general_settings

    def load_search_history(self):
        if path.exists(path.join(SETTINGS_PATH, f"{COMPUTERNAME}_search_history.json")):
            with open(path.join(SETTINGS_PATH, f"{COMPUTERNAME}_search_history.json"), "r") as file:
                self.search_history = OrderedDict(load(file))
                self.remove_old_search_history()
                self.search_bar.addItems(self.search_history.keys())
            
    def load_search_settings(self):
        if path.exists(path.join(SETTINGS_PATH, f"{COMPUTERNAME}_search-settings.json")):
            with open(path.join(SETTINGS_PATH, f"{COMPUTERNAME}_search-settings.json"), "r") as f:
                search_settings = load(f)
        else:
            search_settings = {
                "INDEXED_SEARCH": True,
                "EXCLUDE_PATHS": [
                    "$Recycle.Bin",
                    "$RECYCLE.BIN",
                    "System Volume Information",
                    "Windows",
                    "Program Files",
                    "Program Files (x86)",
                    "ProgramData",
                    "Recovery"
                ],
                "INCLUDE_SUBFOLDERS": False,
                "CACHED_SEARCH": True,
                "HISTORY_LIFETIME": 259200 # 3 days
            }
        return search_settings
        
    def load_tabs(self):
        try:
            with open(path.join(SETTINGS_PATH, f"{COMPUTERNAME}_tabs.json"), "r") as file:
                tabs = load(file)
            for label in tabs.keys():
                self.add_new_tab(label=label, file_path=tabs[label])
        except FileNotFoundError:
            self.add_new_tab()

    def make_tab_unclosable(self, index):
        tab_bar = self.tab_widget.tabBar()
        tab_bar.setTabButton(index, QTabBar.RightSide, None)

    def move_item(self, file_paths: list, destination: str=None):
        if all(path.normpath(path.dirname(file_path)) == destination for file_path in file_paths):
            return
        if self.access.text() == "Write":
            if not destination:
                destination = QFileDialog.getExistingDirectory(self, "Move item to...", file_paths[0])
            for file_path in file_paths:
                file_path = path.normpath(file_path)
                name = path.basename(file_path)
                if destination:
                    try:
                        move(file_path, path.join(destination, name))
                    except PermissionError:
                        name, _ = path.splitext(name)
                        QMessageBox.critical(self, "Permission Error", f"{name} is being used by another process.")
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"Failed to move item: {e}")
            self.undo_history.append(("move", (file_paths, destination)))
        else:
            QMessageBox.information(self, "Permission Error", "You don't have the required permissions.")
        
    def nativeEvent(self, eventType, message):
        native_msg = wintypes.MSG.from_address(int(message.__int__()))
        MSG = native_msg.message
        lParam = native_msg.lParam
        
        if self.is_dragging and self.is_being_dragged:
            if self.is_maximized:
                self.set_geometry()
    
        if MSG == 0xA3:  # WM_NCLBUTTONDBLCLK: Non-client left button double-click
            self.set_geometry()
            return True, 0
        
        if MSG == 0xA1:
            if QApplication.keyboardModifiers() == Qt.KeyboardModifier.ControlModifier:
                Popen(["python", __file__])
            self.is_dragging = True

        # Handle mouse up event
        if MSG == 0xA0:
            if self.is_dragging and self.is_being_dragged:
                cursor_pos = QCursor.pos()
                screen = QApplication.screenAt(cursor_pos)
                if not screen:
                    screen = QApplication.primaryScreen()
                screenGeometry = screen.geometry()

                if self.is_near_edge(cursor_pos, screenGeometry, "top_left"):
                    self.snap_to_top_left(screenGeometry)
                elif self.is_near_edge(cursor_pos, screenGeometry, "top_right"):
                    self.snap_to_top_right(screenGeometry)
                elif self.is_near_edge(cursor_pos, screenGeometry, "bottom_left"):
                    self.snap_to_bottom_left(screenGeometry)
                elif self.is_near_edge(cursor_pos, screenGeometry, "bottom_right"):
                    self.snap_to_bottom_right(screenGeometry)
                elif self.is_near_edge(cursor_pos, screenGeometry, "left"):
                    self.snap_to_left(screenGeometry)
                elif self.is_near_edge(cursor_pos, screenGeometry, "right"):
                    self.snap_to_right(screenGeometry)
                elif self.is_near_edge(cursor_pos, screenGeometry, "top"):
                    self.snap_to_top(screenGeometry)
                elif self.is_near_edge(cursor_pos, screenGeometry, "bottom"):
                    self.snap_to_bottom(screenGeometry)
            
            self.is_dragging = False
            self.is_being_dragged = False
    
        if MSG == 0x84:  # WM_NCHITTESTS
            x, y = fix_coordinate(lParam & 0xFFFF), fix_coordinate(lParam >> 16)
            pos = self.mapFromGlobal(QPoint(x, y))
            
            # Tolerance for edge detection
            tolerance = 8
    
            if abs(pos.y()) < tolerance:  # Top edge
                if abs(pos.x()) < tolerance:
                    return True, 13  # HTTOPLEFT
                elif abs(pos.x() - self.width()) < tolerance:
                    return True, 14  # HTTOPRIGHT
                return True, 12  # HTTOP
            elif abs(pos.y() - self.height()) < tolerance:  # Bottom edge
                if abs(pos.x()) < tolerance:
                    return True, 16  # HTBOTTOMLEFT
                elif abs(pos.x() - self.width()) < tolerance:
                    return True, 17  # HTBOTTOMRIGHT
                return True, 15  # HTBOTTOM
            elif abs(pos.x()) < tolerance:  # Left edge
                return True, 10  # HTLEFT
            elif abs(pos.x() - self.width()) < tolerance:  # Right edge
                return True, 11  # HTRIGHT
    
            if self.title_bar.rect().contains(pos) and not (
                self.title_bar.settings_button.geometry().contains(pos) or
                self.title_bar.minimize_button.geometry().contains(pos) or
                self.title_bar.maximize_restore_button.geometry().contains(pos) or
                self.title_bar.close_button.geometry().contains(pos)
            ):
                self.is_being_dragged = True
                return True, 2  # HTCAPTION
    
        return super().nativeEvent(eventType, message)

    def onCompareComplete(self, output_file_path: str):
        self.undo_history.append(("compare", output_file_path))
        self.comparing = False
        self.search_progress_bar.setProperty("completed", True)
        self.search_progress_bar.style().polish(self.search_progress_bar)
        reset_timer = QTimer(self)
        reset_timer.setSingleShot(True)
        reset_timer.timeout.connect(self.resetProgressBar)
        reset_timer.start(60000)

    def onFoundMatchingFile(self, matches: dict):
        self.search_results_tree.clear()
        for file_path in matches.keys():
            name, file_type, creation_date, modification_date = matches[file_path]
            item = QTreeWidgetItem([name, file_type, file_path, creation_date, modification_date])
            item.setData(0, Qt.ItemDataRole.UserRole, file_path)
            self.search_results_tree.addTopLevelItem(item)
        self.search_progress_bar.setValue(100)
        self.search_progress_bar.setProperty("completed", True)
        self.search_progress_bar.style().polish(self.search_progress_bar)
        self.search_results_dock.setVisible(True)

    def on_item_clicked(self, index: int):
        self.last_clicked_timestamp = QTimer().remainingTime()
        QTimer.singleShot(250, lambda: self.handle_single_click(index))

    def on_item_double_clicked(self, index: int):
        self.handle_single_click(index)
        file_path = self.model.filePath(index)
        if path.isdir(file_path):
            self.browse_folder(file_path)
            self.update_address_bar()
        else:
            self.open_path(file_path)
    
    def onNoMatchingFiles(self):
        QMessageBox.information(self, "File Search", "No matching files found.")

    def on_pinned_item_clicked(self, item: QTreeWidgetItem):
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if path.exists(file_path):
            if path.isdir(file_path):
                self.browse_folder(file_path)
                self.update_address_bar()
            else:
                try:
                    startfile(file_path)
                except Exception as e:
                    QMessageBox.critical(self, "File Open Error", f"There was a problem opening the file:\n{e}")
    
    def onProgressUpdated(self, percent: int):
        if self.search_progress_bar.maximum() == 0:
            self.search_progress_bar.setMaximum(100)
        if percent >= 1: 
            self.search_progress_bar.setValue(percent)

    def onSearchFinished(self, result_count: int, search_time: float):
        if self.search_progress_bar.maximum() == 0:
            self.search_progress_bar.setMaximum(100)
        self.search_info_label.setText(f" Results: {result_count:,} | Search Time: {search_time:.2f} s  ")

    def on_search_result_item_clicked(self, item: QTreeWidgetItem):
        if self.load_general_settings().get("SCROLL_TO_RESULT"):
            file_path = item.data(2, 0)
            index = self.model.index(file_path)
            folder_path = "\\".join(file_path.split("\\")[:-1])
            self.browse_folder(folder_path)
            current_view = self.get_current_view()
            current_view.scrollTo(index)
            current_view.selectionModel().select(index, QItemSelectionModel.SelectionFlag.ClearAndSelect)

    def on_search_result_item_double_clicked(self, item: QTreeWidgetItem):
        file_path = item.data(2, 0)
        if path.isdir(file_path):
            self.browse_folder(file_path)
            self.update_address_bar()
        else:
            self.open_path(file_path)

    def on_source_item_clicked(self, index: int):
        file_path = self.model.filePath(index)
        if path.isdir(file_path):
            self.browse_folder(file_path)
            self.update_address_bar()

    def on_quick_access_clicked(self, item: QTreeWidgetItem):
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if path.exists(file_path):
            self.browse_folder(file_path)
            self.update_address_bar()
            
    def open_item(self):
        current_view = self.get_current_view()
        selected_indexes = current_view.selectedIndexes()
        if selected_indexes:
            index = selected_indexes[0]
        self.on_item_double_clicked(index)

    def open_path(self, file_path: str):
        try:
            startfile(file_path)
        except Exception as e:
            QMessageBox.critical(self, "File Open Error", f"There was a problem opening the file:\n{e}")

    def open_settings(self):
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec()

    def paste_item(self):
        if self.access.text() == "Write":
            mime_data = self.clipboard.mimeData()
            if mime_data.hasUrls():
                file_paths = [url.toLocalFile() for url in mime_data.urls()]
                self.paste_paths(file_paths)
        else:
            QMessageBox.information(self, "Permission Error", "You don't have the required permissions.")

    def paste_paths(self, file_paths: list):
        if self.access.text() == "Write":
            new_paths = []
            replace_all = False
            for item in sorted(file_paths):
                name = path.basename(item)
                destination = path.join(self.current_path, name)
                if path.exists(destination) and not replace_all:
                    dialog = FileReplaceDialog(self, name, len(file_paths))
                    action = dialog.exec()

                    if action == dialog.Replace:
                        pass
                    elif action == dialog.ReplaceAll:
                        replace_all = True
                    elif action == dialog.Rename:
                        name, ext = path.splitext(name)
                        if len(ext) > 1:
                            pretext = name + " - Copy" + ext
                        else:
                            pretext = name + " - Copy"

                        new_name, ok = QInputDialog.getText(self, "File Rename",
                                                            "Enter a new name for the file:",
                                                            text=pretext)
                        if ok and new_name:
                            destination = path.join(self.current_path, new_name)
                        else:
                            continue
                    else:
                        continue

                try:
                    if path.isdir(item):
                        copytree(item, destination)
                    else:
                        copy2(item, destination)
                    new_paths.append(destination)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"An error occurred while pasting: {str(e)}")
                new_paths.append(destination)
            self.undo_history.append(("paste", new_paths))
        else:
            QMessageBox.information(self, "Permission Error", "You don't have the required permissions.")
            
    def pin_to_sidebar(self, file_path: str):
        filename = path.basename(file_path)
        new_name, ok = QInputDialog.getText(self, "Pin Link", "Enter link title:", text=filename)
    
        while ok and not new_name.strip():
            QMessageBox.warning(self, "Error", "Link title cannot be blank.")
            new_name, ok = QInputDialog.getText(self, "Pin Link", "Enter link title:", text=filename)
    
        if ok:
            item = QTreeWidgetItem([new_name])
            item.setData(0, Qt.ItemDataRole.UserRole, file_path)
            self.pinned.addTopLevelItem(item)
            self.save_pinned_items()

    def populate_quick_access(self):
        file_paths = {
            "Desktop": DESKTOP_PATH,
            "Documents": DOCUMENTS_PATH,
            "Downloads": path.expanduser("~\\Downloads"),
            "Pictures": PICTURES_PATH,
            "Videos": path.expanduser("~\\Videos")
        }
        
        for item in listdir(path.expanduser("~")):
            if "OneDrive" in item:
                file_paths[item] = path.expanduser(f"~\\{item}")
                    
        for name, file_path in file_paths.items():
            icon_provider = QFileIconProvider()
            file_info = QFileInfo(file_path)
            icon = icon_provider.icon(file_info)
            tree_item = QTreeWidgetItem(self.quick_access_list)
            tree_item.setText(0, name)
            tree_item.setData(0, Qt.ItemDataRole.UserRole, file_path)
            tree_item.setIcon(0, icon)

    def power_rename(self, file_paths: list):
        if self.access.text() == "Write":
            dialog = PowerRenameDialog(file_paths)
            result = dialog.exec()
            if result == QDialog.Accepted:
                settings = dialog.get_values()
                new_paths = []
                dialog.rename_worker.reset_counter()
                for file_path in file_paths:
                    filename = path.basename(file_path)
                    new_name = dialog.rename_worker.generate_new_name(filename, settings)
                    new_paths.append(file_path.join(path.dirname(file_path), new_name))
                    try:
                        rename(file_path, file_path.join(path.dirname(file_path), new_name))
                    except PermissionError:
                        name, _ = path.splitext(path.basename(file_path))
                        QMessageBox.critical(self, "Permission Error", f"{name} is being used by another process.")
                self.undo_history.append(("powerrename", (file_paths, new_paths)))
        else:
            QMessageBox.information(self, "Permission Error", "You don't have the required permissions.")

    def purge_temp_folder(self):
        if path.exists(TEMP_PATH):
            for file in listdir(TEMP_PATH):
                file_path = path.join(TEMP_PATH, file)
                remove(file_path)

    def relink_pinned_item(self, item: QTreeWidgetItem):
        old_path = item.data(0, Qt.ItemDataRole.UserRole)
        name = item.text(0)

        new_path = QFileDialog.getExistingDirectory(self, "Select New Path", old_path)
        if new_path:
            item.setData(0, Qt.ItemDataRole.UserRole, new_path)

            if name in self.pinned_items:
                self.pinned_items[name] = new_path

            self.save_pinned_items()

    def remove_old_search_history(self):
        current_time = time()
        for item, timestamp in list(self.search_history.items()):
            if current_time and timestamp:
                if current_time - timestamp > self.load_search_settings().get("HISTORY_LIFETIME"):
                    del self.search_history[item]

    def remove_pinned_item(self, item: QTreeWidgetItem):
        file_path = item.data(0, Qt.ItemDataRole.UserRole)
        name = item.text(0)
        if file_path in self.pinned_items.values():
            self.pinned_items.__delitem__(name)

        parent = item.parent()

        if parent is None:
            index = self.pinned.indexOfTopLevelItem(item)
            if index != -1:
                self.pinned.takeTopLevelItem(index)
        else:
            index = parent.indexOfChild(item)
            if index != -1:
                parent.takeChild(index)

        self.save_pinned_items()

    def rename_item(self, file_path: str):
        if self.access.text() == "Write":
            name = path.basename(file_path)
            new_name, ok = QInputDialog.getText(self, "Rename", "Enter new name:", text=name)
            if ok:
                new_path = path.normpath(path.join(path.dirname(file_path), new_name))
                try:
                    rename(file_path, new_path)
                    self.undo_history.append(("rename", (new_path, file_path)))
                except PermissionError:
                        name, _ = path.splitext(name)
                        QMessageBox.critical(self, "Permission Error", f"{name} is being used by another process.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to rename item: {e}")
        else:
            QMessageBox.information(self, "Permission Error", "You don't have the required permissions.")

    def rename_pinned_item(self, item: QTreeWidgetItem):
        old_name = item.text(0)
        file_path = item.data(0, Qt.ItemDataRole.UserRole)

        new_name, ok = QInputDialog.getText(self, "Rename Pinned Item", "Enter new name:", text=old_name)
        if ok and new_name:
            if file_path in self.pinned_items.values():
                for key in list(self.pinned_items.keys()):
                    if self.pinned_items[key] == file_path:
                        self.pinned_items.pop(key)
                        break
                self.pinned_items[new_name] = file_path

            item.setText(0, new_name)
            self.save_pinned_items()

    def resetProgressBar(self, visible=False):
        if not visible:
            self.search_bar.setCurrentText("")
            self.search_progress_bar.setValue(0)
            self.search_progress_bar.setProperty("completed", False)
            self.search_progress_bar.style().polish(self.search_progress_bar)

    def resizeEvent(self, event: QResizeEvent):
        if self.is_maximized:
            self.title_bar.maximize_restore_button.setIcon(self.restore_icon)
            self.title_bar.maximize_restore_button.setIconSize(QSize(18, 18))
        else:
            self.title_bar.maximize_restore_button.setIcon(self.maximize_icon)
            self.title_bar.maximize_restore_button.setIconSize(QSize(13, 13))
        super().resizeEvent(event)

    def save_pinned_items(self):
        items = self.get_items_from_tree(self.pinned)
        with open(path.join(SETTINGS_PATH, f"{COMPUTERNAME}_pinned-items.json"), "w") as f:
            dump(items, f)

    def save_search_history(self):
        with open(path.join(SETTINGS_PATH, f"{COMPUTERNAME}_search_history.json"), "w") as file:
            dump(self.search_history, file)

    def save_tabs(self):
        tabs = {}
        for i in range(self.tab_widget.count()):
            current_view = self.tab_widget.widget(i)
            tabs[self.tab_widget.tabText(i)] =  path.normpath(self.model.filePath(current_view.rootIndex()))
        with open(path.join(SETTINGS_PATH, f"{COMPUTERNAME}_tabs.json"), "w") as file:
            dump(tabs, file)

    def set_geometry(self):
        current_screen = QGuiApplication.screenAt(self.geometry().center())
        if not current_screen:
            current_screen = QGuiApplication.primaryScreen()

        screen_geometry = current_screen.availableGeometry()

        if self.is_maximized:
            self.is_maximized = False
            self.resize(960, 520)
        else:
            self.is_maximized = True
            self.resize(screen_geometry.width(), screen_geometry.height())
            self.move(screen_geometry.x(), screen_geometry.y())
            
    def show_popup(self, title: str, message: str):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def show_process_result(self, processes: set):
        self.search_progress_bar.setMaximum(100)
        if "No matching handles found." in processes:
            QMessageBox.information(self, "File Usage", f"No processes are using the file:\n{self.worker.file_path}")
        else:
            QMessageBox.information(self, "File Usage", processes)

    def show_properties(self, file_path: str):
        self.properties_window = QWidget(self, Qt.WindowType.Window)
        self.properties_window.setObjectName("PropertiesWindow")
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        file_info = QFileInfo(file_path)
        owner = self.get_file_owner(file_path)
        file_icon_provider = QFileIconProvider()

        try:
            file_icon = file_icon_provider.icon(file_info)
        except:
            file_icon = QLineEdit("ERROR")
        try:
            file_type = QLineEdit(file_info.suffix() if not file_info.isDir() else "Directory")
        except:
            file_type = QLineEdit("ERROR")
        try:
            file_path_line = QLineEdit(file_info.absoluteFilePath())
        except:
            file_path_line = QLineEdit("ERROR")
        try:
            file_size = QLineEdit(self.format_file_size(file_info.size()))
        except:
            file_size = QLineEdit("ERROR")
        try:
            date_created = QLineEdit(file_info.birthTime().toString(Qt.DateFormat.SystemLocaleLongDate))
        except:
            date_created = QLineEdit("ERROR")
        try:
            date_modified = QLineEdit(file_info.lastModified().toString(Qt.DateFormat.SystemLocaleLongDate))
        except:
            date_modified = QLineEdit("ERROR")
        try:
            date_accessed = QLineEdit(file_info.lastRead().toString(Qt.DateFormat.SystemLocaleLongDate))
        except:
            date_accessed = QLineEdit("ERROR")
        try:
            file_owner = QLineEdit(owner)
        except:
            file_owner = QLineEdit("ERROR")
        
        file_type_label = QLabel("Type: ")
        file_path_label = QLabel("Location: ")
        file_size_label = QLabel("Size: ")
        date_created_label = QLabel("Date created: ")
        date_modified_label = QLabel("Date modified: ")
        date_accessed_label = QLabel("Date accessed: ")
        file_owner_label = QLabel("Owner: ")
        
        for line_edit in [file_type, file_path_line, file_size, date_created, date_modified, date_accessed, file_owner]:
            if type(line_edit) is QLineEdit:
                line_edit.setReadOnly(True)
                line_edit.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            

        form_layout.addRow(file_type_label, file_type)
        form_layout.addRow(file_path_label, file_path_line)
        form_layout.addRow(file_size_label, file_size)
        form_layout.addRow(date_created_label, date_created)
        form_layout.addRow(date_modified_label, date_modified)
        form_layout.addRow(date_accessed_label, date_accessed)
        form_layout.addRow(file_owner_label, file_owner)
        
        file_type.setObjectName("PropertiesLineEdit")
        file_path_line.setObjectName("PropertiesLineEdit")
        file_size.setObjectName("PropertiesLineEdit")
        date_created.setObjectName("PropertiesLineEdit")
        date_modified.setObjectName("PropertiesLineEdit")
        date_accessed.setObjectName("PropertiesLineEdit")
        file_owner.setObjectName("PropertiesLineEdit")
        
        file_type_label.setObjectName("PropertiesLabel")
        file_path_label.setObjectName("PropertiesLabel")
        file_size_label.setObjectName("PropertiesLabel")
        date_created_label.setObjectName("PropertiesLabel")
        date_modified_label.setObjectName("PropertiesLabel")
        date_accessed_label.setObjectName("PropertiesLabel")
        file_owner_label.setObjectName("PropertiesLabel")
        
        if file_info.isDir():
            num_files, num_dirs = self.get_directory_contents(file_path)
            num_items_text = f"{num_files} Files, {num_dirs} Folders"
            num_items = QLineEdit(num_items_text)
            num_items.setReadOnly(True)
            num_items.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            num_items_label = QLabel("Contains: ")
            num_items.setObjectName("PropertiesLineEdit")
            num_items_label.setObjectName("PropertiesLabel")
            form_layout.addRow(num_items_label, num_items)
            
            dir_size = self.get_directory_size(path)
            dir_size_text = self.format_file_size(dir_size)
            file_size.setText(dir_size_text)
            
        
        layout.addLayout(form_layout)
        self.properties_window.setLayout(layout)
        self.properties_window.setWindowTitle(file_info.fileName() + " Properties")
        self.properties_window.setWindowIcon(file_icon)
        
        self.properties_window.setFixedSize(600, 300)
        
        self.properties_window.show()

    def show_whats_using_file(self, file_path: str):
        self.worker = FileProcessThread(file_path, path.join(BASE_PATH, "handle.exe"))
        self.worker.finished_signal.connect(self.show_process_result)
        self.worker.start()
        self.search_progress_bar.setMaximum(0)

    def snap_to_left(self, screenGeometry):
        newWidth = screenGeometry.width() // 2
        self.setGeometry(screenGeometry.left(), screenGeometry.top(), newWidth, screenGeometry.height())

    def snap_to_right(self, screenGeometry):
        newWidth = screenGeometry.width() // 2
        self.setGeometry(screenGeometry.center().x(), screenGeometry.top(), newWidth, screenGeometry.height())

    def snap_to_top(self, screenGeometry):
        self.setGeometry(screenGeometry.left(), screenGeometry.top(), screenGeometry.width(), screenGeometry.height())

    def snap_to_bottom(self, screenGeometry):
        newHeight = screenGeometry.height() // 2
        self.setGeometry(screenGeometry.left(), screenGeometry.center().y(), screenGeometry.width(), newHeight)

    def snap_to_top_left(self, screenGeometry):
        newWidth = screenGeometry.width() // 2
        newHeight = screenGeometry.height() // 2
        self.setGeometry(screenGeometry.left(), screenGeometry.top(), newWidth, newHeight)
        
    def snap_to_top_right(self, screenGeometry):
        newWidth = screenGeometry.width() // 2
        newHeight = screenGeometry.height() // 2
        self.setGeometry(screenGeometry.center().x(), screenGeometry.top(), newWidth, newHeight)

    def snap_to_bottom_left(self, screenGeometry):
        newWidth = screenGeometry.width() // 2
        newHeight = screenGeometry.height() // 2
        self.setGeometry(screenGeometry.left(), screenGeometry.center().y(), newWidth, newHeight)

    def snap_to_bottom_right(self, screenGeometry):
        newWidth = screenGeometry.width() // 2
        newHeight = screenGeometry.height() // 2
        self.setGeometry(screenGeometry.center().x(), screenGeometry.center().y(), newWidth, newHeight)

    def start_comparing(self):
        if not self.compare_thread or not self.compare_thread.isRunning():
            self.comparing = True
            self.search_progress_bar.setProperty("completed", False)
            self.search_progress_bar.setMaximum(0)
            self.search_progress_bar.style().polish(self.search_progress_bar)
            current_view = self.get_current_view()
            indices = current_view.selectedIndexes()
            file_paths = []
            for index in indices:
                if self.model.filePath(index) not in file_paths:
                    file_paths.append(self.model.filePath(index))
            self.compare_thread = CompareThread(file_paths)
            self.compare_thread.progressUpdated.connect(self.onProgressUpdated)
            self.compare_thread.compareComplete.connect(self.onCompareComplete)
            self.compare_thread.popupSignal.connect(self.show_popup)
            self.compare_thread.start()

    def start_searching(self): 
        if not self.search_thread or not self.search_thread.isRunning():
            query = self.search_bar.currentText().strip()
            self.searching = True
            self.search_progress_bar.setProperty("completed", False)
            self.search_progress_bar.setMaximum(0)
            self.search_progress_bar.style().polish(self.search_progress_bar)
            if query:
                self.search_history[query] = time()
                self.search_history.move_to_end(query, last=False)
                self.save_search_history()
            self.search_bar.clear()
            self.search_bar.setCurrentText(query)
            self.search_bar.addItems(self.search_history.keys())
            self.search_thread = FileSearchThread(query, self.address_bar.text(), self.index_count, self.index_cache, mode=0 if "All Drives" in self.search_bar.placeholderText() else 1)
            self.search_thread.noMatchingFiles.connect(self.onNoMatchingFiles)
            self.search_thread.searchFinished.connect(self.onSearchFinished)
            self.search_thread.foundMatchingFile.connect(self.onFoundMatchingFile)
            self.search_thread.progressUpdated.connect(self.onProgressUpdated)
            self.search_thread.start()
        else:
            self.stop_searching()

    def stop_searching(self):
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.stop()
            self.search_thread.quit()
            self.search_progress_bar.setValue(0)
            self.search_progress_bar.setProperty("completed", False)
            self.search_progress_bar.style().polish(self.search_progress_bar)

    def toggle_preview(self):
        self.preview_dock.setVisible(not self.preview_dock.isVisible())
        self.preview.update_preview()

    def toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def trash_item(self, file_paths: list):
        if self.access.text() == "Write":
            if not path.exists(TEMP_PATH):
                mkdir(TEMP_PATH)
            names = []
            old_paths = []
            first = True
            for file_path in file_paths:
                file_path = path.normpath(file_path)
                if len(file_paths) == 1:
                    reply = QMessageBox.question(self, "Delete Item", f"Are you sure you want to move '{file_path}' to the recycling bin?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                elif len(file_paths) > 1 and first is True:
                    reply = QMessageBox.question(self, "Delete Item", f"Are you sure you want to move {len(file_path)} files to the recycling bin?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                    first = False
                if reply == QMessageBox.StandardButton.Yes:
                    name = path.basename(file_path)
                    names.append(path.basename(path))
                    old_paths.append(path.dirname(file_path))
                    try:
                        if path.isfile(file_path):
                            copy2(file_path, TEMP_PATH)
                        else:
                            copytree(path, path.join(TEMP_PATH, name))
                        send2trash(path)
                    except PermissionError:
                        name, _ = path.splitext(name)
                        QMessageBox.critical(self, "Permission Error", f"{name} is being used by another process.")
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"Failed to move to recycling bin: {e}")
                    self.update_file_count()
            self.undo_history.append(("trash", (names, old_paths)))
        else:
            QMessageBox.information(self, "Permission Error", "You don't have the required permissions.")

    def undo_operation(self):
        if self.undo_history:
            last_operation, data = self.undo_history.pop()
            
            if last_operation == "compress":
                # data: path
                if path.exists(data):
                    remove(data)
                
            elif last_operation == "new-file":
                # data: path
                if path.exists(data):
                    remove(data)
                
            elif last_operation == "new-folder":
                # data: path
                if path.exists(data):
                    rmdir(data)
                
            elif last_operation == "new-shortcut":
                # data: path
                if path.exists(data):
                    remove(data)
                
            elif last_operation == "extract":
                # data: path
                if path.exists(data):
                    remove(data)
            
            elif last_operation == "move":
                # data: (paths, destination)
                for old_path in data[0]:
                    old_path = path.normpath(old_path)
                    new_path = data[1] + "\\" + path.basename(old_path)
                    if path.exists(new_path):
                        self.shutil.move(new_path, old_path)
            
            elif last_operation == "compare":
                # data: path
                if path.exists(data):
                    remove(data)
            
            elif last_operation == "paste":
                # data: new_paths
                for file_path in data:
                    if path.exists(file_path):
                        remove(file_path)
            
            elif last_operation == "pin":
                # data: QTopLevelItem
                self.remove_pinned_item(data)
            
            elif last_operation == "powerrename":
                # data: (old_paths, new_paths)
                for i in range(len(data[0])):
                    if path.exists(data[1][i]):
                        rename(data[1][i], data[0][i])
            
            elif last_operation == "rename":
                # data: (new_path, path)
                if path.exists(data[0]):
                    rename(data[0], data[1])
            
            elif last_operation == "trash":
                # data: names, old destinations
                for i in range(len(data[0])):
                    file_path = path.join(TEMP_PATH, data[0][i])
                    if path.exists(file_path):
                        move(file_path, data[1][i])

    def update_address_bar(self):
        current_view = self.get_current_view()
        if current_view:
            current_path = path.normpath(self.model.filePath(current_view.rootIndex()))
            self.current_path = current_path
            self.address_bar.set_path(current_path)
            self.update_file_count()

    def update_details_bar(self):
        current_view = self.get_current_view()
        if current_view:
            current_path = path.normpath(self.model.filePath(current_view.currentIndex()))

        if path.exists(current_path):
            name, ext = path.splitext(path.basename(current_path))
            file_info = QFileInfo(current_path)
            
            file_size = self.format_file_size(file_info.size())
            date_created = file_info.birthTime().toString(Qt.DateFormat.TextDate)
            file_owner = self.get_file_owner(current_path).split("\\")[-1]
            page_info = ""
            if ext.lower() == ".pdf":
                page_count = self.preview.page_count
                current_page = self.preview.current_page + 1
                page_info = f"Page {current_page}/{page_count}"
            details_message = f"{page_info}  |  Owner: {file_owner} |  Size: {file_size}  |  Created: {date_created}"
            self.details_bar.setText(details_message)

    def update_file_count(self):
        try:
            file_count = len(listdir(self.current_path))
            self.file_count_label.setText(f"File Count: {file_count:,}")
        except NotADirectoryError:
            file_count = "NIL"
            self.file_count_label.setText(f"File Count: {file_count}")
        except FileNotFoundError:
            file_count = "NIL"
            self.file_count_label.setText(f"File Count: {file_count}")

    def update_indexing_labels(self, text: str, indexed_count: int, index_cache: dict):
        self.index_cache = index_cache
        self.index_count = indexed_count
        self.status_label.setText(text)
        self.index_label.setText(f"Indexed Items: {indexed_count:,}")
