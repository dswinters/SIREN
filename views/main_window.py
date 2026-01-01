from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton)
from models import InstrumentModel, ScaleModel
from controls import PresetSelector, OffsetController, ColormapDropdown
from .fretboard import FretboardView
from .scale_selector import ScaleSelectorView
from .polygon import PolygonView

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

        self.btn_clear = QPushButton("Deactivate All Notes")
        self.btn_reset = QPushButton("Activate All Notes")
        
        self.btn_polygon = QPushButton("Polygon View")
        self.btn_polygon.clicked.connect(self.open_polygon_view)
        
        self.btn_clear.clicked.connect(self.scale_model.deactivate_all_notes)
        self.btn_reset.clicked.connect(self.scale_model.activate_all_notes)

        self.colormap_selector = ColormapDropdown()
        self.colormap_selector.currentIndexChanged.connect(self.on_colormap_changed)

        self.preset_selector = PresetSelector()
        self.preset_selector.currentTextChanged.connect(self.change_tuning)

        self.offset_controller = OffsetController(self.instrument_model)

        top_bar = QHBoxLayout()
        top_bar.addWidget(self.preset_selector)
        top_bar.addWidget(self.offset_controller)
        top_bar.addWidget(self.btn_polygon)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_reset)
        top_bar.addWidget(self.btn_clear)
        top_bar.addWidget(self.colormap_selector)
        
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

    def open_polygon_view(self):
        if not hasattr(self, 'polygon_window') or not self.polygon_window.isVisible():
            self.polygon_window = PolygonView(self.scale_model)
            self.polygon_window.set_colormap(self.colormap_selector.itemData(self.colormap_selector.currentIndex()))
            self.polygon_window.show()
        else:
            self.polygon_window.raise_()
            self.polygon_window.activateWindow()

    def on_colormap_changed(self, index):
        name = self.colormap_selector.itemData(index)
        self.update_colormaps(name)

    def update_colormaps(self, name):
        self.fret_view.set_colormap(name)
        self.scale_view.set_colormap(name)
        if hasattr(self, 'polygon_window') and self.polygon_window:
            self.polygon_window.set_colormap(name)

    def change_tuning(self, name):
        tuning = self.preset_selector.get_tuning(name)
        if tuning:
            self.instrument_model.set_tuning(tuning)
