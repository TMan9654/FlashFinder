
from ...utils.utils import load_settings, save_settings

from PySide6.QtWidgets import QWidget, QGroupBox, QLabel, QCheckBox, QComboBox, QVBoxLayout, QFormLayout


class GeneralSettings(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.general_settings = load_settings("general")
        self.RELOAD_MAIN_TAB = self.general_settings.get("RELOAD_MAIN_TAB")
        self.SCROLL_TO = self.general_settings.get("SCROLL_TO")
        self.EXTERNAL_DROP_MODE = self.general_settings.get("EXTERNAL_DROP_MODE")
        self.init_ui()

    def init_ui(self):
        main_group = QGroupBox()
        
        self.main_tab_label = QLabel("Main Tab Behaviour:")
        self.main_tab_checkbox = QCheckBox('Load "Main" last session on startup.')
        self.main_tab_checkbox.setChecked(self.RELOAD_MAIN_TAB)
        self.main_tab_checkbox.stateChanged.connect(self.reload_main_tab)
        
        self.scroll_to_label = QLabel("Scroll to:")
        self.scroll_to_checkbox = QCheckBox("Scroll to item in main view on click for the search results.")
        self.scroll_to_checkbox.setChecked(self.SCROLL_TO)
        self.scroll_to_checkbox.stateChanged.connect(self.scroll_to)
        
        self.drop_action_label = QLabel("External Drop Action:")
        self.drop_action_combobox = QComboBox(self)
        self.drop_action_combobox.addItems(["Paste", "Move"])
        self.drop_action_combobox.setCurrentText(self.EXTERNAL_DROP_MODE)
        self.drop_action_combobox.currentTextChanged.connect(self.set_drop_mode)
                
        main_layout = QVBoxLayout()
        main_group_layout = QFormLayout()
        
        main_group_layout.addRow(self.main_tab_label, self.main_tab_checkbox)
        main_group_layout.addRow(self.scroll_to_label, self.scroll_to_checkbox)
        main_group_layout.addRow(self.drop_action_label, self.drop_action_combobox)

        main_group.setLayout(main_group_layout)
        
        main_layout.addWidget(main_group)
        
        self.setLayout(main_layout)
        
        # self.setStyleSheet("""
        #     QLabel {
        #         color: black;
        #         font: 14px Arial, sans-serif;
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
        #     """)
        
    def reload_main_tab(self, state: int):
        if state == 2:
            self.general_settings["RELOAD_MAIN_TAB"] = True
        else:
            self.general_settings["RELOAD_MAIN_TAB"] = False
        save_settings("general", self.general_settings)
        
    def set_drop_mode(self, mode: str):
        self.general_settings["EXTERNAL_DROP_MODE"] = mode
        save_settings("general", self.general_settings)
    
    def scroll_to(self, state: int):
        if state == 2:
            self.general_settings["SCROLL_TO"] = True
        else:
            self.general_settings["SCROLL_TO"] = False
        save_settings("general", self.general_settings)
       