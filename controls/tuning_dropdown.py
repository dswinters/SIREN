import os
import yaml
from PySide6.QtWidgets import QComboBox

class TuningDropdown(QComboBox):
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