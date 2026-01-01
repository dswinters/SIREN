from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QComboBox)
from models import InstrumentModel, ScaleModel
from .fretboard import FretboardView
from .scale_selector import ScaleSelectorView
from .common import CYCLIC_MAPS

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Guitar Scales Explorer")
        self.resize(1200, 600)

        self.instrument_model = InstrumentModel()
        self.scale_model = ScaleModel()
        self.fret_view = FretboardView(self.instrument_model, self.scale_model)
        self.scale_view = ScaleSelectorView(self.scale_model)

        self.btn_left = QPushButton("<")
        self.btn_right = QPushButton(">")
        for b in [self.btn_left, self.btn_right]:
            b.setFixedWidth(30)
            b.setStyleSheet("font-weight: bold; font-size: 14px;")

        # Inverted direction for visual intuition: 
        # Right Arrow -> Content moves Left (Next items appear) -> Offset +1
        # Left Arrow -> Content moves Right (Prev items appear) -> Offset -1
        self.btn_right.clicked.connect(lambda: self.scale_model.rotate_view(1))
        self.btn_left.clicked.connect(lambda: self.scale_model.rotate_view(-1))

        self.btn_append = QPushButton("Add String (High)")
        self.btn_prepend = QPushButton("Add String (Low)")
        self.btn_remove = QPushButton("Remove String")
        self.btn_clear = QPushButton("Deactivate All Notes")
        self.btn_reset = QPushButton("Activate All Notes")
        
        self.btn_append.clicked.connect(self.instrument_model.append_string)
        self.btn_prepend.clicked.connect(self.instrument_model.prepend_string)
        self.btn_remove.clicked.connect(self.instrument_model.remove_string)
        self.btn_clear.clicked.connect(self.scale_model.deactivate_all_notes)
        self.btn_reset.clicked.connect(self.scale_model.activate_all_notes)

        self.combo_maps = QComboBox()
        self.combo_maps.addItems(CYCLIC_MAPS)
        self.combo_maps.currentTextChanged.connect(self.update_colormaps)

        top_bar = QHBoxLayout()
        top_bar.addWidget(self.btn_remove)
        top_bar.addWidget(self.btn_prepend)
        top_bar.addWidget(self.btn_append)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_reset)
        top_bar.addWidget(self.btn_clear)
        top_bar.addWidget(self.combo_maps)
        
        scale_layout = QHBoxLayout()
        scale_layout.setContentsMargins(0, 10, 0, 0)
        scale_layout.addWidget(self.btn_left)
        scale_layout.addWidget(self.btn_right)
        scale_layout.addWidget(self.scale_view)

        layout = QVBoxLayout()
        layout.addLayout(top_bar)
        layout.addWidget(self.fret_view)
        layout.addLayout(scale_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def update_colormaps(self, name):
        self.fret_view.set_colormap(name)
        self.scale_view.set_colormap(name)
