
from ..config.config import ICONS_PATH

from os import path
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPixmapCache, QIcon
from PySide6.QtWidgets import QFileSystemModel


class FileSystemModel(QFileSystemModel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.icon_paths = {
            ".sldprt": path.join(ICONS_PATH, "part.png"),
            ".sldasm": path.join(ICONS_PATH, "assembly.png"),
            ".slddrw": path.join(ICONS_PATH, "drawing2.png")
        }
        self.SWdir_icon_path = path.join(ICONS_PATH, "SWdir.png")
        
        self.icon_cache = QPixmapCache()
        for icon_path in self.icon_paths.values():
            pixmap = QPixmap(icon_path)
            self.icon_cache.insert(pixmap)
        self.icon_cache.insert(QPixmap(self.SWdir_icon_path))

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if index.column() == 0 and role == Qt.ItemDataRole.DecorationRole:
            file_name = self.filePath(index)
            file_ext = path.splitext(file_name)[1].lower()

            if file_name.startswith("C:/SWPDM/MX_PDM") and self.isDir(index):
                return self._getCachedIcon(self.SWdir_icon_path)
            elif file_ext in self.icon_paths.keys():
                icon_path = self.icon_paths[file_ext]
                return self._getCachedIcon(icon_path)
            
        if index.column() == 1 and role == Qt.ItemDataRole.DisplayRole:
            size_in_bytes = self.size(index)
            return self._format_size(size_in_bytes)

        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignLeft

        return super().data(index, role)
    
    def _getCachedIcon(self, icon_path):
        pixmap = QPixmapCache.find(icon_path)
        if pixmap is None:
            pixmap = QPixmap(icon_path)
            QPixmapCache.insert(icon_path, pixmap)
        return QIcon(pixmap)
    
    def _format_size(self, size_in_bytes):
        suffixes = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
        if size_in_bytes == 0:
            return ""
        i = 0
        while size_in_bytes >= 1000 and i < len(suffixes)-1:
            size_in_bytes /= 1000.0
            i += 1
        return f"{size_in_bytes:.2f} {suffixes[i]}"
