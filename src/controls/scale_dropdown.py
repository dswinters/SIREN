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
                data = yaml.safe_load(f)
        except FileNotFoundError:
            data = {}

        if data:
            # Check if it's the new categorized format (values are lists)
            if isinstance(next(iter(data.values())), list):
                for category, scales in data.items():
                    self.addItem(category)
                    # Disable category header
                    self.model().item(self.count() - 1).setEnabled(False)

                    for scale_entry in scales:
                        for name, value in scale_entry.items():
                            self.addItem(f"  {name}", value)
            else:
                # Legacy flat format
                for name, value in data.items():
                    self.addItem(name, value)

        self.currentIndexChanged.connect(self.on_selection)

    def on_selection(self, index):
        if index <= 0: return

        val = self.itemData(index)
        if val is not None:
            self.scale_model.set_value(int(val))

        self.blockSignals(True)
        self.setCurrentIndex(0)
        self.blockSignals(False)