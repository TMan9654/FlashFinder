from ..utils.utils import load_settings
from ..gui.progress_window import ProgressWindow

from os import path

import fitz
from tempfile import TemporaryDirectory
from numpy import array, where, all, int32
from PIL import Image, ImageChops, ImageDraw, ImageOps
from cv2 import findContours, threshold, approxPolyDP, arcLength, contourArea, boundingRect, THRESH_BINARY, RETR_EXTERNAL, CHAIN_APPROX_SIMPLE
from PySide6.QtCore import QThread, Signal

class CompareThread(QThread):
    progressUpdated = Signal(int)
    compareComplete = Signal(int)
    logMessage = Signal(str)
    
    def __init__(self, files: list[str], progress_window: ProgressWindow, parent=None):
        super(CompareThread, self).__init__(parent)
        compare_settings = load_settings("compare")
        self.DPI_LEVEL = compare_settings.get("DPI_LEVEL")
        self.PAGE_SIZE = tuple(compare_settings.get("PAGE_SIZES").get(compare_settings.get("PAGE_SIZE")))
        self.INCLUDE_IMAGES = compare_settings.get("INCLUDE_IMAGES")
        self.MAIN_PAGE= compare_settings.get("MAIN_PAGE")
        self.THRESHOLD = compare_settings.get("THRESHOLD")
        self.MIN_AREA = compare_settings.get("MIN_AREA")
        self.EPSILON = compare_settings.get("EPSILON")
        self.OUTPUT_PATH = compare_settings.get("OUTPUT_PATH")
        self.SCALE_OUTPUT = compare_settings.get("SCALE_OUTPUT")
        self.OUTPUT_BW = compare_settings.get("OUTPUT_BW")
        self.OUTPUT_GS = compare_settings.get("OUTPUT_GS")
        self.REDUCE_FILESIZE = compare_settings.get("REDUCE_FILESIZE")
        self.files = files
        self.progress_window = progress_window
        self.statistics = {
            "NUM_PAGES": 0,
            "MAIN_PAGE": None,
            "TOTAL_DIFFERENCES": 0,
            "PAGES_WITH_DIFFERENCES": []
            }
        
        self.progressUpdated.connect(self.progress_window.update_progress)
        self.logMessage.connect(self.progress_window.update_log)
        self.compareComplete.connect(self.progress_window.operation_complete)
    
    def run(self):
        try:
            self.handle_files(self.files)
        except fitz.FileDataError as e:
            self.logMessage.emit(f"Error opening file: {e}")
            self.compareComplete.emit(5)

    def mark_differences(self, page_num: int, image1: Image.Image, image2: Image.Image) -> list[Image.Image]:
        # Overlay Image
        if self.INCLUDE_IMAGES["Overlay"] is True:
            if image1.size != image2.size:
                image2.size = image2.resize(image1.size)
                self.logMessage.emit("Comparison", "Page sizes don't match and the 'Scale Pages' setting is off, attempting to match page sizes... results may be inaccurate.")
            image1array = array(image1)
            image2array = array(image2)
            image2array[~all(image2array == [255, 255, 255], axis=-1)] = [255, 0, 0] # Convert non-white pixels in image2array to red for overlay.
            overlay_image = Image.fromarray(where(all(image1array == [255, 255, 255], axis=-1, keepdims=True), image2array, image1array))
            del image1array, image2array
            
        # Markup Image / Differences Image
        if self.INCLUDE_IMAGES["Markup"] is True or self.INCLUDE_IMAGES["Difference"] is True:
            diff_image = Image.fromarray(where(all(array(ImageOps.colorize(ImageOps.invert(ImageChops.subtract(image2, image1).convert("L")), black="blue", white="white").convert("RGB")) == [255, 255, 255], axis=-1)[:,:,None], array(ImageOps.colorize(ImageOps.invert(ImageChops.subtract(image1, image2).convert("L")), black="red", white="white").convert("RGB")), array(ImageOps.colorize(ImageOps.invert(ImageChops.subtract(image2, image1).convert("L")), black="blue", white="white").convert("RGB"))))
            if self.INCLUDE_IMAGES["Markup"] is True:
                contours, _ = findContours(threshold(array(ImageChops.difference(image2, image1).convert("L")), self.THRESHOLD, 255, THRESH_BINARY)[1], RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)
                del _
                marked_image = Image.new("RGBA", image1.size, (255, 0, 0, 255))
                marked_image.paste(image1, (0, 0))
                marked_image_draw = ImageDraw.Draw(marked_image)
                
                previous_differences = self.statistics["TOTAL_DIFFERENCES"]

                for contour in contours:
                    approx = approxPolyDP(contour, (self.EPSILON + 0.0000000001) * arcLength(contour, False), False)
                    marked_image_draw.line(tuple(map(tuple, array(approx).reshape((-1, 2)).astype(int32))), fill=(255, 0, 0, 255), width=int(self.DPI_LEVEL/100))
                    if contourArea(contour) > self.MIN_AREA:
                        x, y, w, h = boundingRect(approx)
                        diff_box = Image.new("RGBA", (w, h), (0, 255, 0, 64))
                        ImageDraw.Draw(diff_box).rectangle([(0, 0), (w - 1, h - 1)], outline=(255, 0, 0, 255))
                        marked_image.paste(diff_box, (x, y), mask=diff_box)
                        self.statistics["TOTAL_DIFFERENCES"] += 1
                        del diff_box, x, y, w, h
                    del approx
                self.statistics["PAGES_WITH_DIFFERENCES"].append((page_num, self.statistics["TOTAL_DIFFERENCES"] - previous_differences))
                del contours, marked_image_draw

        # Output
        output = []
        if not self.SCALE_OUTPUT:
            if self.INCLUDE_IMAGES["New Copy"]:
                output.append(image1.resize((int(self.PAGE_SIZE[0] * self.DPI_LEVEL), int(self.PAGE_SIZE[1] * self.DPI_LEVEL))) if self.MAIN_PAGE == "New Document" else image2.resize((int(self.PAGE_SIZE[0] * self.DPI_LEVEL), int(self.PAGE_SIZE[1] * self.DPI_LEVEL))))
            if self.INCLUDE_IMAGES["Old Copy"]:
                output.append(image2.resize((int(self.PAGE_SIZE[0] * self.DPI_LEVEL), int(self.PAGE_SIZE[1] * self.DPI_LEVEL))) if self.MAIN_PAGE == "New Document" else image1.resize((int(self.PAGE_SIZE[0] * self.DPI_LEVEL), int(self.PAGE_SIZE[1] * self.DPI_LEVEL))))
            if self.INCLUDE_IMAGES["Markup"]:
                output.append(marked_image.resize((int(self.PAGE_SIZE[0] * self.DPI_LEVEL), int(self.PAGE_SIZE[1] * self.DPI_LEVEL))))
            if self.INCLUDE_IMAGES["Difference"]:
                output.append(diff_image.resize((int(self.PAGE_SIZE[0] * self.DPI_LEVEL), int(self.PAGE_SIZE[1] * self.DPI_LEVEL))))
            if self.INCLUDE_IMAGES["Overlay"]:
                output.append(overlay_image.resize((int(self.PAGE_SIZE[0] * self.DPI_LEVEL), int(self.PAGE_SIZE[1] * self.DPI_LEVEL))))
        else:
            if self.INCLUDE_IMAGES["New Copy"]:
                output.append(image1 if self.MAIN_PAGE == "New Document" else image2)
            if self.INCLUDE_IMAGES["Old Copy"]:
                output.append(image2 if self.MAIN_PAGE == "New Document" else image1)
            if self.INCLUDE_IMAGES["Markup"]:
                output.append(marked_image)
            if self.INCLUDE_IMAGES["Difference"]:
                output.append(diff_image)
            if self.INCLUDE_IMAGES["Overlay"]:
                output.append(overlay_image)
        return output
    
    def pdf_to_image(self, page_number: int, doc: fitz.Document) -> Image.Image:
        if page_number < doc.page_count:
            pix = doc.load_page(page_number).get_pixmap(dpi=self.DPI_LEVEL)
            image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        else:
            pix = doc.load_page(0).get_pixmap(dpi=self.DPI_LEVEL)
            image = Image.new("RGB", (pix.width, pix.height), (255, 255, 255))
        del pix
        if self.SCALE_OUTPUT is True:
            image = image.resize((int(self.PAGE_SIZE[0] * self.DPI_LEVEL), int(self.PAGE_SIZE[1] * self.DPI_LEVEL)))
        return image

    def handle_files(self, files: list[str]) -> str:
        self.logMessage.emit(f"""Processing files:
    {files[0]}
    {files[1]}""")
        current_progress = 0
        with fitz.open(files[0 if self.MAIN_PAGE == "New Document" else 1]) as doc1, fitz.open(files[0 if self.MAIN_PAGE == "OLD" else 1]) as doc2:
            size = doc1.load_page(0).rect
            # If page size is auto, self.PAGESIZE will be none
            if self.PAGE_SIZE[0] is None:
                # Assume 72 DPI for original document resolution
                self.PAGE_SIZE = (size.width / 72, size.height / 72)
            self.statistics["MAIN_PAGE"] = files[0 if self.MAIN_PAGE == "New Document" else 1]
            filename = files[0 if self.MAIN_PAGE == "New Document" else 1].split("/")[-1]
            source_path = False
            if self.OUTPUT_PATH is None:
                self.OUTPUT_PATH = files[0].replace(filename, "")
                source_path = True
            
            total_operations = max(doc1.page_count, doc2.page_count)
            self.logMessage.emit(f"Total pages {total_operations}.")
            progress_per_operation = 100.0 / total_operations

            self.logMessage.emit("Creating temporary directory...")
            with TemporaryDirectory() as temp_dir:
                self.logMessage.emit(f"Temporary directory created: {temp_dir}")
                image_files = []
                stats_filename = path.join(temp_dir, "stats.pdf")
                image_files.append(stats_filename)

                for i in range(total_operations):
                    self.logMessage.emit(f"Processing page {i+1} of {total_operations}...")
                    self.logMessage.emit(f"Converting main page...")
                    image1 = self.pdf_to_image(i, doc1)
                    self.logMessage.emit(f"Converting secondary page...")
                    image2 = self.pdf_to_image(i, doc2)
                    self.logMessage.emit(f"Marking differences...")
                    markups = self.mark_differences(i, image1, image2)
                    del image1, image2

                    # Save marked images
                    self.logMessage.emit(f"Saving output files...")
                    for j, image in enumerate(markups):
                        if self.OUTPUT_GS is True:
                            image = image.convert("L")
                        if self.OUTPUT_BW is True:
                            image = image.convert("1")
                        else:
                            image = image.convert("RGB")
                        image_file = path.join(temp_dir, f"{i}_{j}.pdf")
                        image.save(image_file, resolution=self.DPI_LEVEL, author="MAXFIELD", optimize=self.REDUCE_FILESIZE)
                        del image
                        image_files.append(image_file)
                        
                    current_progress += progress_per_operation
                    self.progressUpdated.emit(int(current_progress))

                # Create statistics page
                text = f"Document Comparison Report\n\nTotal Pages: {total_operations}\nFiles Compared:\n    {files[0]}\n    {files[1]}\nMain Page: {self.statistics['MAIN_PAGE']}\nTotal Differences: {self.statistics['TOTAL_DIFFERENCES']}\nPages with differences:\n"
                for page_info in self.statistics["PAGES_WITH_DIFFERENCES"]:
                    text += f"    Page {page_info[0]+1} Changes: {page_info[1]}\n"

                # Create statistics page and handle text overflow
                stats_doc = fitz.open()
                stats_page = stats_doc.new_page()
                text_blocks = text.split('\n')
                y_position = 72
                for line in text_blocks:
                    if y_position > fitz.paper_size('letter')[1] - 72:
                        stats_page = stats_doc.new_page()  # Create a new page if needed
                        y_position = 72  # Reset y position for the new page
                    stats_page.insert_text((72, y_position), line, fontsize=11, fontname="helv")
                    y_position += 12  # Adjust y_position by the line height

                # Save and close the stats document
                stats_filename = path.join(temp_dir, "stats.pdf")
                stats_doc.save(stats_filename)
                stats_doc.close()

                # Builds final PDF from each PDF image page
                self.logMessage.emit("Compiling PDF from output folder...")
                compiled_pdf = fitz.open()
                for img_path in image_files:
                    img = fitz.open(img_path)
                    compiled_pdf.insert_pdf(img, links=False)
                    img.close()
                
                # Save Final PDF File
                self.logMessage.emit(f"Saving final PDF...")
                output_path = f"{self.OUTPUT_PATH}{filename.split('.')[0]} Comparison.pdf"
                output_iterator = 0
                
                # Checks if a version alreaday exists and increments revision if necessary
                while path.exists(output_path):
                    output_iterator += 1
                    output_path = f"{self.OUTPUT_PATH}{filename.split('.')[0]} Comparison Rev {output_iterator}.pdf"
                compiled_pdf.save(output_path)
                compiled_pdf.close()

                self.logMessage.emit(f"Comparison file created: {output_path}")
                if source_path:
                    self.OUTPUT_PATH = None

        self.compareComplete.emit(5)
        return output_path
            