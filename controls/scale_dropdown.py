import os
import yaml
from PySide6.QtWidgets import QComboBox

class ScaleSelectDropdown(QComboBox):
    def __init__(self, scale_model):
        super().__init__()
        self.scale_model = scale_model
        self.addItem("Select scale")
        
        # Load scales
        config_path = os.path.join(os.path.dirname(__file__), "../config/scales.yaml")
        try:
            with open(config_path, 'r') as f:
                self.scales = yaml.safe_load(f)
        except FileNotFoundError:
            self.scales = {}
            
        if self.scales:
            for name in self.scales:
                self.addItem(name)
            
        self.currentIndexChanged.connect(self.on_selection)
        
    def on_selection(self, index):
        if index <= 0: return
        
        name = self.currentText()
        if name in self.scales:
            # Convert 1/0 list to boolean list
            mask = [bool(x) for x in self.scales[name]]
            self.scale_model.set_mask(mask)
            
        self.blockSignals(True)
        self.setCurrentIndex(0)
        self.blockSignals(False)