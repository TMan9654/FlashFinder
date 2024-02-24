
from ..config.config import SETTINGS_PATH, COMPUTERNAME

from os import path

import fitz
from json import load
from numpy import array, where, all, int32
from PIL import Image, ImageChops, ImageDraw, ImageOps
from cv2 import findContours, threshold, approxPolyDP, arcLength, contourArea, boundingRect, THRESH_BINARY, RETR_EXTERNAL, CHAIN_APPROX_SIMPLE
from PySide6.QtCore import QThread, Signal

class CompareThread(QThread):
    progressUpdated = Signal(int)
    compareComplete = Signal(str)
    popupSignal = Signal(str, str)

    def __init__(self, files:list, parent=None):
        super(CompareThread, self).__init__(parent)
        self.compare_settings_path = path.join(SETTINGS_PATH, f"{COMPUTERNAME}_compare-settings.json")
        compare_settings = self.load_settings()
        self.DPI_LEVEL = compare_settings.get("DPI_LEVEL")
        self.PAGE_SIZE = tuple(compare_settings.get("PAGE_SIZES").get(compare_settings.get("PAGE_NAME")))
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
    
    def run(self):
        output_file_path = self.handle_files(self.files)
        self.compareComplete.emit(output_file_path)

    def mark_differences(self, image1, image2):
        if self.INCLUDE_IMAGES["Overlay"] is True:
            if image1.size != image2.size:
                image2.size = image2.resize(image1.size)
                self.popupSignal.emit("Comparison", "Page sizes don't match and the 'Scale Pages' setting is off, attempting to match page sizes... results may be inaccurate.")
            image1array = array(image1)
            image2array = array(image2)
            image1array[all(image1array != [255, 255, 255], axis=-1)] = [255, 0, 0]
            overlay_image = Image.fromarray(where(all(image2array == [255, 255, 255], axis=-1, keepdims=True), image1array, image2array))
            del image1array, image2array
        if self.INCLUDE_IMAGES["Markup"] is True or self.INCLUDE_IMAGES["Difference"] is True:
            diff_image = Image.fromarray(where(all(array(ImageOps.colorize(ImageOps.invert(ImageChops.subtract(image1, image2).convert("L")), black="blue", white="white").convert("RGB")) == [255, 255, 255], axis=-1)[:,:,None], array(ImageOps.colorize(ImageOps.invert(ImageChops.subtract(image2, image1).convert("L")), black="red", white="white").convert("RGB")), array(ImageOps.colorize(ImageOps.invert(ImageChops.subtract(image1, image2).convert("L")), black="blue", white="white").convert("RGB"))))
            if self.INCLUDE_IMAGES["Markup"] is True:
                contours, _ = findContours(threshold(array(ImageChops.difference(image1, image2).convert("L")), self.THRESHOLD, 255, THRESH_BINARY)[1], RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)
                del _
                marked_image = Image.new("RGBA", image1.size, (255, 0, 0, 255))
                marked_image.paste(image2, (0, 0))
                marked_image_draw = ImageDraw.Draw(marked_image)
                for contour in contours:
                    approx = approxPolyDP(contour, (self.EPSILON + 0.0000000001) * arcLength(contour, False), False)
                    marked_image_draw.line(tuple(map(tuple, array(approx).reshape((-1, 2)).astype(int32))), fill=(255, 0, 0, 255), width=int(self.DPI_LEVEL/100))
                    if contourArea(contour) > self.MIN_AREA:
                        x, y, w, h = boundingRect(approx)
                        diff_box = Image.new("RGBA", (w, h), (0, 255, 0, 64))
                        ImageDraw.Draw(diff_box).rectangle([(0, 0), (w - 1, h - 1)], outline=(255, 0, 0, 255))
                        marked_image.paste(diff_box, (x, y), mask=diff_box)
                        del diff_box, x, y, w, h
                    del approx
                del contours, marked_image_draw
        output = []
        if self.SCALE_OUTPUT is False:
            if self.INCLUDE_IMAGES["New Copy"] is True:
                output.append(image1.resize((int(self.PAGE_SIZE[0] * self.DPI_LEVEL), int(self.PAGE_SIZE[1] * self.DPI_LEVEL))) if self.MAIN_PAGE == "New Document" else image2.resize((int(self.PAGE_SIZE[0] * self.DPI_LEVEL), int(self.PAGE_SIZE[1] * self.DPI_LEVEL))))
            if self.INCLUDE_IMAGES["Old Copy"] is True:
                output.append(image2.resize((int(self.PAGE_SIZE[0] * self.DPI_LEVEL), int(self.PAGE_SIZE[1] * self.DPI_LEVEL))) if self.MAIN_PAGE == "New Document" else image1.resize((int(self.PAGE_SIZE[0] * self.DPI_LEVEL), int(self.PAGE_SIZE[1] * self.DPI_LEVEL))))
            if self.INCLUDE_IMAGES["Markup"] is True:
                output.append(marked_image.resize((int(self.PAGE_SIZE[0] * self.DPI_LEVEL), int(self.PAGE_SIZE[1] * self.DPI_LEVEL))))
            if self.INCLUDE_IMAGES["Difference"] is True:
                output.append(diff_image.resize((int(self.PAGE_SIZE[0] * self.DPI_LEVEL), int(self.PAGE_SIZE[1] * self.DPI_LEVEL))))
            if self.INCLUDE_IMAGES["Overlay"] is True:
                output.append(overlay_image.resize((int(self.PAGE_SIZE[0] * self.DPI_LEVEL), int(self.PAGE_SIZE[1] * self.DPI_LEVEL))))
        else:
            if self.INCLUDE_IMAGES["New Copy"] is True:
                output.append(image1 if self.MAIN_PAGE == "New Document" else image2)
            if self.INCLUDE_IMAGES["Old Copy"] is True:
                output.append(image2 if self.MAIN_PAGE == "New Document" else image1)
            if self.INCLUDE_IMAGES["Markup"] is True:
                output.append(marked_image)
            if self.INCLUDE_IMAGES["Difference"] is True:
                output.append(diff_image)
            if self.INCLUDE_IMAGES["Overlay"] is True:
                output.append(overlay_image)
        return output

    def pdf_to_image(self, pdf_path:str, i:int) -> Image:
        with fitz.open(pdf_path) as doc:
            if i < doc.page_count:
                pix = doc.load_page(i).get_pixmap(dpi=self.DPI_LEVEL)
                image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            else:
                pix = doc.load_page(0).get_pixmap(dpi=self.DPI_LEVEL)
                image = Image.new("RGB", (pix.width, pix.height), (255, 255, 255))
            del pix
            if self.SCALE_OUTPUT is True:
                image = image.resize((int(self.PAGE_SIZE[0] * self.DPI_LEVEL), int(self.PAGE_SIZE[1] * self.DPI_LEVEL)))
        return image

    def sort_files(self, files: list) -> list:
        sorted_files = []
        previous_file = None
        for file in files:
            file = file.split("\\")[-1]
            if previous_file is not None:
                if len(file) > len(previous_file):
                    sorted_files.append(file)
                    sorted_files.append(previous_file)
                else:
                    sorted_files = sorted(files)
            previous_file = file
        return sorted_files

    def handle_files(self, files: list) -> str:
        from tempfile import TemporaryDirectory     
        with fitz.open(files[0 if self.MAIN_PAGE == "New Document" else 1]) as doc1, fitz.open(files[0 if self.MAIN_PAGE == "New Document" else 1]) as doc2:
            size = doc1.load_page(0).rect
            if self.PAGE_SIZE[0] is None:
                # 72 is DPI of originals???
                self.PAGE_SIZE = (size.width/72, size.height/72)
            files = self.sort_files(files)
            filename = files[1 if self.MAIN_PAGE == "New Document" else 0].split("/")[-1]
            source_path = False
            if self.OUTPUT_PATH is None:
                self.OUTPUT_PATH = files[1].replace(filename, "")
                source_path = True
            toc = []

            total_operations = max(doc1.page_count, doc2.page_count)
            progress_per_operation = 100.0 / total_operations
            current_progress = 0

            with TemporaryDirectory() as temp_dir:
                temp_pdf_path = path.join(temp_dir, "temp_output.pdf")
                for i in range(total_operations):
                    # Process the first PDF page to image
                    image1 = self.pdf_to_image(files[0 if self.MAIN_PAGE == "New Document" else 1], i)
                    current_progress += progress_per_operation * 0.1
                    self.progressUpdated.emit(int(current_progress))
                    
                    # Process the second PDF page to image
                    image2 = self.pdf_to_image(files[1 if self.MAIN_PAGE == "New Document" else 0], i)
                    current_progress += progress_per_operation * 0.1
                    self.progressUpdated.emit(int(current_progress))
                    
                    # Mark differences
                    markup = self.mark_differences(image1, image2)
                    current_progress += progress_per_operation * 0.2
                    self.progressUpdated.emit(int(current_progress))
                    del image1, image2
                    
                    current_progress += progress_per_operation * 0.5
                    self.progressUpdated.emit(int(current_progress))
                    
                    output = []
                    if self.INCLUDE_IMAGES["Old Copy"] is True:
                        output.append("Old Copy")
                    if self.INCLUDE_IMAGES["New Copy"] is True:
                        output.append("New Copy")
                    if self.INCLUDE_IMAGES["Markup"] is True:
                        output.append("Markup")
                    if self.INCLUDE_IMAGES["Difference"] is True:
                        output.append("Difference")
                    if self.INCLUDE_IMAGES["Overlay"] is True:
                        output.append("Overlay")
                    for j, name in enumerate(output):
                        toc.append([1, f"{name} - Pg {i+1}", i+j])
                        if self.OUTPUT_GS is True:
                            image = markup[j].convert("L")
                        if self.OUTPUT_BW is True:
                            image = markup[j].convert("1")
                        else:
                            image = markup[j].convert("RGB")
                        try:
                            if path.exists(temp_pdf_path) is False:
                                image.save(temp_pdf_path, resolution=self.DPI_LEVEL, author="MAXFIELD", optimize=self.REDUCE_FILESIZE)
                            else:
                                image.save(temp_pdf_path, resolution=self.DPI_LEVEL, optimize=self.REDUCE_FILESIZE, append=True)
                        except Exception:
                            if path.exists(temp_pdf_path + " - Copy.pdf") is False:
                                image.save(temp_pdf_path + " - Copy.pdf", resolution=self.DPI_LEVEL, author="MAXFIELD", optimize=self.REDUCE_FILESIZE)
                            else:
                                image.save(temp_pdf_path + " - Copy.pdf", resolution=self.DPI_LEVEL, optimize=self.REDUCE_FILESIZE, append=True)
                    del markup

                    current_progress += progress_per_operation * 0.1
                    self.progressUpdated.emit(int(current_progress))

                output_path = f"{self.OUTPUT_PATH}{filename.split('.')[0]} Comparison.pdf"
                with fitz.open(temp_pdf_path) as pdf:
                    pdf.set_toc(toc)
                    output_iterator = 0
                    while path.exists(output_path):
                        output_iterator += 1
                        output_path = f"{self.OUTPUT_PATH}{filename.split('.')[0]} Comparison Rev {output_iterator}.pdf"
                    pdf.save(output_path, encryption=fitz.PDF_ENCRYPT_KEEP)
                        
            if source_path is True:
                self.OUTPUT_PATH = None
            
            return output_path
                
    def load_settings(self) -> dict:
        if path.exists(self.compare_settings_path):
            with open(self.compare_settings_path, "r") as f:
                settings = load(f)
        else:
            settings = {
                "PAGE_SIZES": {
                    "AUTO": [None, None],
                    "LETTER": [8.5, 11],
                    "ANSI A": [11, 8.5],
                    "ANSI B": [17, 11],
                    "ANSI C": [22, 17],
                    "ANSI D": [34, 22]
                },
                "DPI_LEVELS": [75, 150, 300, 600, 1200, 1800],
                "DPI_LABELS": [
                    "Low DPI: Draft Quality [75]",
                    "Low DPI: Viewing Only [150]",
                    "Medium DPI: Printable [300]",
                    "Standard DPI [600]",
                    "High DPI [1200]: Professional Quality",
                    "Max DPI [1800]: Large File Size"
                ],
                "INCLUDE_IMAGES": {"New Copy": False, "Old Copy": False, "Markup": True, "Difference": True, "Overlay": True},
                "DPI": "Standard DPI [600]",
                "DPI_LEVEL": 600,
                "PAGE_NAME": "ANSI B",
                "THRESHOLD": 128,
                "MIN_AREA": 100,
                "EPSILON": 0.0,
                "OUTPUT_PATH": None,
                "SCALE_OUTPUT": False,
                "OUTPUT_BW": False,
                "OUTPUT_GS": False,
                "REDUCE_FILESIZE": True,
                "MAIN_PAGE": "New Document"
            }
        return settings
