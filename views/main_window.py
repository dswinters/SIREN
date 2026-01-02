from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel)
from PySide6.QtCore import Qt
from models import InstrumentModel, ScaleModel
from controls import PresetSelector, OffsetController, ColormapDropdown
from controls.scale_dropdown import ScaleSelectDropdown
from .fretboard import FretboardView
from .scale_selector import ScaleSelectorView
from .polygon import PolygonView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Guitar Scales Explorer")
        self.resize(2400, 400)

        self.instrument_model = InstrumentModel()
        self.scale_model = ScaleModel()
        self.fret_view = FretboardView(self.instrument_model, self.scale_model)
        self.scale_view = ScaleSelectorView(self.scale_model)

        self.btn_left = QPushButton("<")
        self.btn_right = QPushButton(">")
        self.btn_trans_left = QPushButton("<")
        self.btn_trans_right = QPushButton(">")
        
        for b in [self.btn_left, self.btn_right, self.btn_trans_left, self.btn_trans_right]:
            b.setFixedWidth(30)
            b.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.btn_left.setToolTip("Rotate Mode")
        self.btn_right.setToolTip("Rotate Mode")
        self.btn_trans_left.setToolTip("Transpose -1")
        self.btn_trans_right.setToolTip("Transpose +1")

        # Inverted direction for visual intuition: 
        # Right Arrow -> Content moves Left (Next items appear) -> Offset +1
        # Left Arrow -> Content moves Right (Prev items appear) -> Offset -1
        self.btn_right.clicked.connect(lambda: self.rotate_modes(1))
        self.btn_left.clicked.connect(lambda: self.rotate_modes(-1))
        self.btn_trans_left.clicked.connect(lambda: self.scale_model.transpose(-1))
        self.btn_trans_right.clicked.connect(lambda: self.scale_model.transpose(1))

        self.btn_clear = QPushButton("Deactivate All Notes")
        self.btn_reset = QPushButton("Activate All Notes")
        
        self.btn_polygon = QPushButton("Polygon View")
        self.btn_polygon.clicked.connect(self.open_polygon_view)
        
        self.btn_clear.clicked.connect(self.scale_model.deactivate_all_notes)
        self.btn_reset.clicked.connect(self.scale_model.activate_all_notes)

        self.colormap_selector = ColormapDropdown()
        self.colormap_selector.currentIndexChanged.connect(self.on_colormap_changed)

        self.scale_dropdown = ScaleSelectDropdown(self.scale_model)

        self.lbl_mode = QLabel("Change Mode")
        self.lbl_mode.setAlignment(Qt.AlignCenter)
        self.lbl_mode.setStyleSheet("font-size: 10px; font-weight: bold; color: #888;")
        
        self.lbl_trans = QLabel("Transpose")
        self.lbl_trans.setAlignment(Qt.AlignCenter)
        self.lbl_trans.setStyleSheet("font-size: 10px; font-weight: bold; color: #888;")

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
        
        ctrl_layout = QVBoxLayout()
        ctrl_layout.addWidget(self.lbl_mode)
        row1 = QHBoxLayout()
        row1.addWidget(self.btn_left)
        row1.addWidget(self.btn_right)
        ctrl_layout.addLayout(row1)
        
        ctrl_layout.addWidget(self.lbl_trans)
        row2 = QHBoxLayout()
        row2.addWidget(self.btn_trans_left)
        row2.addWidget(self.btn_trans_right)
        ctrl_layout.addLayout(row2)
        ctrl_layout.addWidget(self.scale_dropdown)
        
        scale_layout.addLayout(ctrl_layout)
        scale_layout.addWidget(self.scale_view)

        layout = QVBoxLayout()
        layout.addLayout(top_bar)
        layout.addWidget(self.fret_view)
        layout.addLayout(scale_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def rotate_modes(self, direction):
        if self.scale_view.is_animating():
            return
        if hasattr(self, 'polygon_window') and self.polygon_window.isVisible() and self.polygon_window.is_animating():
            return
        self.scale_model.rotate_modes(direction)

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
