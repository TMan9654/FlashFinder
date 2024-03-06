
from fitz import open as fopen
from PySide6.QtCore import QByteArray, QEvent, Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QMessageBox, QGraphicsTextItem, QApplication

class PreviewWindow(QGraphicsView):

    def __init__(self, parent=None):
        super(PreviewWindow, self).__init__(parent)
        self.preview_scene = QGraphicsScene(self)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        self.setScene(self.preview_scene)
        self.page_count = 0
        self.current_page = 0
        self.last_page = 0
        self.zoom_level = 1.0
        self.pdf_document = None
        self.explorer = self.parent()
        self.last_index = None
        self.loaded = False

    def update_preview(self):
        if not self.explorer.preview_dock.isVisible():
            return
        index = self.explorer.get_current_view().currentIndex()
        if index != self.last_index:
            self.zoom_level = 1
            self.resetTransform()
            self.loaded = False

        file_path = self.explorer.model.filePath(index)
        lower_path = file_path.lower()
        if index != self.last_index or self.current_page != self.last_page:
            self.preview_scene.clear()
            if lower_path.endswith((".png", ".jpg", ".jpeg", ".bmp")):
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    self.preview_scene.addItem(QGraphicsPixmapItem(pixmap))
                else:
                    self._add_text_to_scene("Unable to preview this file.")

            elif lower_path.endswith(".pdf"):
                self._load_pdf(file_path)

            elif lower_path.endswith((".txt", ".py", ".pyw", ".js", ".html", ".cpp", ".c", ".rs")):
                self._load_text_file(file_path)

            else:
                self._add_text_to_scene("No preview available.")

        self.last_index = index
        self._adjust_view()
        self.explorer.update_details_bar()

    def _load_pdf(self, file_path: str):
        try:
            with fopen(file_path) as pdf_document:
                self.page_count = pdf_document.page_count
                if self.current_page >= self.page_count:
                    self.current_page = 0

                page = pdf_document.load_page(self.current_page)
                
                svg = page.get_svg_image()
                svg_item = QGraphicsSvgItem()
                svg_item.setSharedRenderer(QSvgRenderer(QByteArray(svg.encode("utf-8"))))
                self.preview_scene.addItem(svg_item)

        except Exception as e:
            QMessageBox.critical(self, "File Read Error", f"There was an error reading the file for previewing: {e}")

    def _load_text_file(self, file_path: str):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                preview_text = f.read()
                text_item = self._add_text_to_scene(preview_text)
                self.setSceneRect(text_item.boundingRect())
        except Exception as e:
            self._add_text_to_scene(f"Unable to preview this file. Reason: {e}")

    def _add_text_to_scene(self, text: str):
        text_item = QGraphicsTextItem(text)
        font = text_item.font()
        font.setPointSize(12)
        text_item.setFont(font)
        self.preview_scene.addItem(text_item)
        return text_item

    def _adjust_view(self):
        self.setSceneRect(self.preview_scene.itemsBoundingRect())
        self.fitInView(self.preview_scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.scale(self.zoom_level, self.zoom_level)

    def wheelEvent(self, event: QEvent):
        if not self.preview_scene:
            return

        modifiers = QApplication.keyboardModifiers()
        delta = event.angleDelta().y()

        if modifiers == Qt.ControlModifier:
            zoom_in_factor = 1.15
            zoom_out_factor = 0.85

            factor = zoom_in_factor if delta > 0 else zoom_out_factor

            min_zoom_level = 1.0
            max_zoom_level = 25.0

            new_zoom_level = self.zoom_level * factor
            if min_zoom_level <= new_zoom_level <= max_zoom_level:
                self.zoom_level = new_zoom_level
                self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
                self.scale(factor, factor)
                self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)

        elif modifiers == Qt.ShiftModifier:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta)
        
        else:
            vbar = self.verticalScrollBar()
            at_bottom = vbar.value() >= vbar.maximum()
            at_top = vbar.value() <= vbar.minimum()
            if delta > 0 and at_top and self.current_page > 0:
                self.last_page = self.current_page
                self.current_page -= 1
                self.update_preview()
                self.explorer.update_details_bar()
            elif delta < 0 and at_bottom and self.current_page < self.page_count - 1:
                self.last_page = self.current_page
                self.current_page += 1
                self.update_preview()
                self.explorer.update_details_bar()
            else:
                super().wheelEvent(event)

