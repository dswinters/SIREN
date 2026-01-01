import os
import yaml
from PySide6.QtWidgets import QComboBox, QWidget, QHBoxLayout, QPushButton

class PresetSelector(QComboBox):
    def __init__(self, config_file="config/tunings.yaml"):
        super().__init__()
        self.tunings = {}
        self._load_tunings(config_file)
        self.addItems(list(self.tunings.keys()))

    def _load_tunings(self, config_file):
        if not os.path.exists(config_file):
            return
        
        try:
            with open(config_file, 'r') as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict):
                    self.tunings = data
        except Exception as e:
            print(f"Error loading tunings: {e}")

    def get_tuning(self, name):
        return self.tunings.get(name)

class OffsetController(QWidget):
    def __init__(self, instrument_model):
        super().__init__()
        self.model = instrument_model
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.btn_minus = QPushButton("-")
        self.btn_plus = QPushButton("+")
        
        for btn in [self.btn_minus, self.btn_plus]:
            btn.setFixedWidth(30)
            layout.addWidget(btn)
            
        self.setLayout(layout)
        
        self.btn_minus.clicked.connect(lambda: self.model.set_tuning([(n - 1) % 12 for n in self.model.tuning]))
        self.btn_plus.clicked.connect(lambda: self.model.set_tuning([(n + 1) % 12 for n in self.model.tuning]))