
from ...utils.utils import load_settings, save_settings

from os import path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QLabel, QComboBox, QLineEdit, QCheckBox, QGroupBox, QFormLayout, QHBoxLayout, \
    QVBoxLayout


class CompareSettings(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.compare_settings = load_settings("compare")
        self.PAGE_SIZES = self.compare_settings.get("PAGE_SIZES")
        self.DPI_LEVELS = self.compare_settings.get("DPI_LEVELS")
        self.DPI_LABELS = self.compare_settings.get("DPI_LABELS")
        self.INCLUDE_IMAGES = self.compare_settings.get("INCLUDE_IMAGES")
        self.DPI = self.compare_settings.get("DPI", "Medium DPI: Printable [300]")
        self.DPI_LEVEL = self.compare_settings.get("DPI_LEVEL")
        self.PAGE_NAME = self.compare_settings.get("PAGE_NAME")
        self.THRESHOLD = self.compare_settings.get("THRESHOLD")
        self.MIN_AREA = self.compare_settings.get("MIN_AREA")
        self.EPSILON = self.compare_settings.get("EPSILON")
        self.OUTPUT_PATH = self.compare_settings.get("OUTPUT_PATH")
        self.SCALE_OUTPUT = self.compare_settings.get("SCALE_OUTPUT")
        self.OUTPUT_BW = self.compare_settings.get("OUTPUT_BW")
        self.OUTPUT_GS = self.compare_settings.get("OUTPUT_GS")
        self.REDUCE_FILESIZE = self.compare_settings.get("REDUCE_FILESIZE")
        self.MAIN_PAGE = self.compare_settings.get("MAIN_PAGE")
        self.init_ui()
        
    def init_ui(self):
        self.dpi_level_label = QLabel("DPI Level:")
        self.dpi_level_combobox = QComboBox(self)
        self.dpi_level_combobox.addItems(self.DPI_LABELS)
        self.dpi_level_combobox.setCurrentText(self.DPI)
        self.dpi_level_combobox.currentTextChanged.connect(self.set_dpi_level)
        self.page_size_label = QLabel("Page Size:")
        self.page_size_combobox = QComboBox(self)
        self.page_size_combobox.addItems(self.PAGE_SIZES)
        self.page_size_combobox.setCurrentText(self.PAGE_NAME)
        self.page_size_combobox.currentTextChanged.connect(self.set_page_size)
        self.output_path_label = QLabel("Output Path:")
        self.output_path_combobox = QComboBox(self)
        self.output_path_combobox.addItems(["Source Path", "Default Path", "Specified Path"])
        if self.OUTPUT_PATH == "\\": 
            self.output_path_combobox.setCurrentText("Default Path")
        elif self.OUTPUT_PATH is None:
            self.output_path_combobox.setCurrentText("Source Path")
        else:
            self.output_path_combobox.setCurrentText("Specified Path")
        self.output_path_combobox.currentTextChanged.connect(self.set_output_path)

        self.specified_label = QLabel("Specified Path:")
        self.specified_entry = QLineEdit(self)
        self.specified_entry.setText(self.OUTPUT_PATH if self.output_path_combobox.currentText() == "Specified Path" else "")
        self.specified_entry.textChanged.connect(self.set_output_path)

        self.checkbox_image1 = QCheckBox("New Copy")
        self.checkbox_image1.setChecked(self.INCLUDE_IMAGES.get("New Copy", False))
        self.checkbox_image2 = QCheckBox("Old Copy")
        self.checkbox_image2.setChecked(self.INCLUDE_IMAGES.get("Old Copy", False))
        self.checkbox_image3 = QCheckBox("Markup")
        self.checkbox_image3.setChecked(self.INCLUDE_IMAGES.get("Markup", False))
        self.checkbox_image4 = QCheckBox("Difference")
        self.checkbox_image4.setChecked(self.INCLUDE_IMAGES.get("Difference", True))
        self.checkbox_image5 = QCheckBox("Overlay")
        self.checkbox_image5.setChecked(self.INCLUDE_IMAGES.get("Overlay", False))
        self.checkbox_image1.stateChanged.connect(self.set_output_images)
        self.checkbox_image2.stateChanged.connect(self.set_output_images)
        self.checkbox_image3.stateChanged.connect(self.set_output_images)
        self.checkbox_image4.stateChanged.connect(self.set_output_images)
        self.checkbox_image5.stateChanged.connect(self.set_output_images)

        self.scaling_checkbox = QCheckBox("Scale Pages")
        self.scaling_checkbox.setChecked(self.SCALE_OUTPUT)
        self.scaling_checkbox.stateChanged.connect(self.set_scaling)
        self.bw_checkbox = QCheckBox("Black/White")
        self.bw_checkbox.setChecked(self.OUTPUT_BW)
        self.bw_checkbox.stateChanged.connect(self.set_bw)
        self.gs_checkbox = QCheckBox("Grayscale")
        self.gs_checkbox.setChecked(self.OUTPUT_GS)
        self.gs_checkbox.stateChanged.connect(self.set_gs)
        self.reduce_checkbox = QCheckBox("Reduce Size")
        self.reduce_checkbox.setChecked(self.REDUCE_FILESIZE)
        self.reduce_checkbox.stateChanged.connect(self.set_reduced_filesize)

        self.main_page_label = QLabel("Main Page:")
        self.main_page_combobox = QComboBox(self)
        self.main_page_combobox.addItems(["New Document", "Old Document"])
        self.main_page_combobox.setCurrentText(self.MAIN_PAGE)
        self.main_page_combobox.currentTextChanged.connect(self.set_main_page)
        
        output_path_group = QGroupBox("Output Settings")
        include_images_group = QGroupBox("Files to include:")
        general_group = QGroupBox("General")
        checkboxes_group = QGroupBox()
        other_group = QGroupBox()
        
        output_path_layout = QFormLayout(output_path_group)
        output_path_layout.addRow(self.dpi_level_label, self.dpi_level_combobox)
        output_path_layout.addRow(self.page_size_label, self.page_size_combobox)
        output_path_layout.addRow(self.output_path_label, self.output_path_combobox)
        output_path_layout.addRow(self.specified_label, self.specified_entry)
        output_path_group.setLayout(output_path_layout)

        include_images_layout = QHBoxLayout(include_images_group)
        include_images_layout.addWidget(self.checkbox_image1)
        include_images_layout.addWidget(self.checkbox_image2)
        include_images_layout.addWidget(self.checkbox_image3)
        include_images_layout.addWidget(self.checkbox_image4)
        include_images_layout.addWidget(self.checkbox_image5)
        include_images_group.setLayout(include_images_layout)
        
        general_layout = QHBoxLayout(general_group)
        checkboxes = QVBoxLayout(checkboxes_group)
        other = QVBoxLayout(other_group)
        other.setAlignment(Qt.AlignmentFlag.AlignTop)
        checkboxes.addWidget(self.scaling_checkbox)
        checkboxes.addWidget(self.bw_checkbox)
        checkboxes.addWidget(self.gs_checkbox)
        checkboxes.addWidget(self.reduce_checkbox)
        other.addWidget(self.main_page_label)
        other.addWidget(self.main_page_combobox)
        checkboxes_group.setLayout(checkboxes)
        other_group.setLayout(other)
        general_layout.addWidget(checkboxes_group)
        general_layout.addWidget(other_group)
        general_group.setLayout(general_layout)
        
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.addWidget(output_path_group)
        main_layout.addWidget(include_images_group)
        main_layout.addWidget(general_group)
        
        self.setLayout(main_layout)
        # self.setStyleSheet("""
        #     QLabel {
        #         color: black;
        #         font: 14px Arial, sans-serif;
        #     }
        #     QSpinBox {
        #         color: black;
        #         font: 14px Arial, sans-serif;
        #         border: 1px solid #ccc;
        #         padding: 5px;
        #         background-color: #f0f0f0;
        #     }
        #     QComboBox { 
        #         background-color: #FFFFFF; 
        #         color: #333; 
        #         font: 14px Arial, sans-serif;
        #         border: 1px solid #CCC; 
        #     }
        #     QComboBox:hover { 
        #         background-color: #EDEDED; 
        #     }
        #     QComboBox:focus { 
        #         background-color: #E5E5E5; 
        #     }
        #     QComboBox:disabled { 
        #         background-color: #FAFAFA; 
        #         color: #888; 
        #         border: 1px solid #CCC; 
        #     }
        #     QComboBox QAbstractItemView { 
        #         background-color: #FFFFFF; 
        #         color: #333; 
        #         selection-background-color: #E0E0E0; 
        #         selection-color: #333; 
        #         border: 1px solid #CCC; 
        #     }
        #     QCheckBox {
        #         color: black;
        #         font: 14px Arial, sans-serif;
        #     }
        #     QLineEdit {
        #         color: black;
        #         font: 14px Arial, sans-serif;
        #         border: 1px solid #ccc;
        #         padding: 5px;
        #         background-color: #f0f0f0;
        #     }
        #     QGroupBox {
        #         font: 14px Arial, sans-serif;
        #         border: 1px solid #ccc;
        #         margin-top: 1em;
        #         background-color: #f0f0f0;
        #     }
        #     QGroupBox::title {
        #         subcontrol-origin: margin;
        #         left: 10px;
        #         padding: 0 3px 0 3px;
        #     }
        #     QFormLayout {
        #         margin: 5px;
        #         border: 1px solid #ccc;
        #         background-color: #f0f0f0;
        #     }
        #     QWidget {
        #         background-color: #f0f0f0;
        #     }
        # """)
            
    def set_dpi_level(self, DPI: str):
        if DPI != "":
            self.compare_settings["DPI"] = DPI
            self.compare_settings["DPI_LEVEL"] = self.DPI_LEVELS[self.DPI_LABELS.index(DPI)]
        save_settings("compare", self.compare_settings)
    
    def set_page_size(self, page_size: str):
        self.compare_settings["PAGE_NAME"] = page_size
        self.compare_settings["PAGE_SIZE"] = self.PAGE_SIZES[page_size]
        save_settings("compare", self.compare_settings)

    def set_output_path(self, option: str):
        if option == "Source Path":
            self.compare_settings["OUTPUT_PATH"] = None
        elif option == "Default Path":
            self.compare_settings["OUTPUT_PATH"] = path.expanduser("~\\Documents")
        else:
            self.compare_settings["OUTPUT_PATH"] = self.specified_entry.text()
            self.compare_settings["OUTPUT_PATH"] = self.compare_settings["OUTPUT_PATH"].replace("\\", "\\\\")
            self.compare_settings["OUTPUT_PATH"] += "\\"
        save_settings("compare", self.compare_settings)

    def set_output_images(self, state: int):
        checkbox = self.sender()
        if state == 2:
            self.compare_settings["INCLUDE_IMAGES"][checkbox.text()] = True
        else:
            self.compare_settings["INCLUDE_IMAGES"][checkbox.text()] = False
        save_settings("compare", self.compare_settings)
    
    def set_scaling(self, state: int):
        if state == 2:
            self.compare_settings["SCALE_OUTPUT"] = True
        else:
            self.compare_settings["SCALE_OUTPUT"] = False
        save_settings("compare", self.compare_settings)
                    
    def set_bw(self, state: int):
        if state == 2:
            self.compare_settings["OUTPUT_BW"] = True
        else:
            self.compare_settings["OUTPUT_BW"] = False
        save_settings("compare", self.compare_settings)
                    
    def set_gs(self, state: int):
        if state == 2:
            self.compare_settings["OUTPUT_GS"] = True
        else:
            self.compare_settings["OUTPUT_GS"] = False
        save_settings("compare", self.compare_settings)
    
    def set_reduced_filesize(self, state: int):
        if state == 2:
            self.compare_settings["REDUCE_FILESIZE"] = True
        else:
            self.compare_settings["REDUCE_FILESIZE"] = False
        save_settings("compare", self.compare_settings)
                    
    def set_main_page(self, page: str):
        self.compare_settings["MAIN_PAGE"] = page
        save_settings("compare", self.compare_settings)
