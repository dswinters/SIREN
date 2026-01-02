from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QComboBox, QStackedWidget,
                               QCheckBox, QLineEdit)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIntValidator
from models import InstrumentModel, ScaleModel
from modules.sound import SoundEngine
from controls import PresetSelector, OffsetController, ColormapDropdown
from controls.scale_dropdown import ScaleSelectDropdown
from .fretboard import FretboardView
from .scale_selector import ScaleSelectorView
from .piano import PianoView
from .polygon import PolygonView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Guitar Scales Explorer")
        self.resize(2400, 400)

        self.instrument_model = InstrumentModel()
        self.scale_model = ScaleModel()
        self.fret_view = FretboardView(self.instrument_model, self.scale_model)
        self.piano_view = PianoView(self.scale_model)
        self.scale_view = ScaleSelectorView(self.scale_model)
        
        self.sound_engine = SoundEngine()
        self.sound_engine.playback_stopped.connect(self.on_playback_stopped)
        self.scale_model.updated.connect(self.on_scale_updated)

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
        
        self.view_selector = QComboBox()
        self.view_selector.addItems(["Fretboard", "Piano"])
        self.view_selector.currentIndexChanged.connect(self.switch_view)
        
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
        
        # Sound Controls
        self.lbl_sound = QLabel("Sound")
        self.lbl_sound.setAlignment(Qt.AlignCenter)
        self.lbl_sound.setStyleSheet("font-size: 10px; font-weight: bold; color: #888;")
        
        self.btn_play = QPushButton("Play")
        self.btn_play.clicked.connect(self.toggle_playback)
        
        self.chk_loop = QCheckBox("Loop")
        self.chk_loop.toggled.connect(self.sound_engine.set_looping)

        self.btn_oct_down = QPushButton("Oct -")
        self.btn_oct_up = QPushButton("Oct +")
        for b in [self.btn_oct_down, self.btn_oct_up]:
            b.setFixedWidth(40)
            b.setStyleSheet("font-size: 10px; font-weight: bold;")
        self.btn_oct_down.clicked.connect(lambda: self.sound_engine.change_octave(-1))
        self.btn_oct_up.clicked.connect(lambda: self.sound_engine.change_octave(1))
        
        self.txt_bpm = QLineEdit("120")
        self.txt_bpm.setValidator(QIntValidator(1, 999))
        self.txt_bpm.setPlaceholderText("BPM")
        self.txt_bpm.textChanged.connect(self.sound_engine.set_bpm)
        
        self.cmb_instrument = QComboBox()
        self.cmb_instrument.addItems(self.sound_engine.get_available_instruments())
        self.cmb_instrument.currentTextChanged.connect(self.sound_engine.set_instrument)

        self.preset_selector = PresetSelector()
        self.preset_selector.currentTextChanged.connect(self.change_tuning)

        self.offset_controller = OffsetController(self.instrument_model)

        top_bar = QHBoxLayout()
        top_bar.addWidget(self.preset_selector)
        top_bar.addWidget(self.offset_controller)
        top_bar.addWidget(self.btn_polygon)
        top_bar.addWidget(self.view_selector)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_reset)
        top_bar.addWidget(self.btn_clear)
        top_bar.addWidget(self.colormap_selector)
        
        self.central_stack = QStackedWidget()
        self.central_stack.addWidget(self.fret_view)
        self.central_stack.addWidget(self.piano_view)
        
        scale_layout = QHBoxLayout()
        scale_layout.setContentsMargins(0, 10, 0, 0)
        
        ctrl_container = QWidget()
        ctrl_container.setFixedWidth(180)
        ctrl_layout = QVBoxLayout(ctrl_container)
        ctrl_layout.setContentsMargins(0, 0, 0, 0)
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
        
        ctrl_layout.addWidget(self.lbl_sound)
        ctrl_layout.addWidget(self.btn_play)
        ctrl_layout.addWidget(self.chk_loop)
        row_oct = QHBoxLayout()
        row_oct.addWidget(self.btn_oct_down)
        row_oct.addWidget(self.btn_oct_up)
        ctrl_layout.addLayout(row_oct)
        ctrl_layout.addWidget(self.txt_bpm)
        ctrl_layout.addWidget(self.cmb_instrument)
        
        scale_layout.addWidget(ctrl_container)
        scale_layout.addWidget(self.scale_view)

        layout = QVBoxLayout()
        layout.addLayout(top_bar)
        layout.addWidget(self.central_stack)
        layout.addLayout(scale_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def switch_view(self, index):
        self.central_stack.setCurrentIndex(index)

    def toggle_playback(self):
        if self.sound_engine.is_playing:
            self.sound_engine.stop()
            self.btn_play.setText("Play")
        else:
            self.sound_engine.update_scale(self.scale_model.rotation_offset, self.scale_model.mask)
            self.sound_engine.play()
            self.btn_play.setText("Stop")

    @Slot()
    def on_playback_stopped(self):
        self.btn_play.setText("Play")

    def on_scale_updated(self):
        self.sound_engine.update_scale(self.scale_model.rotation_offset, self.scale_model.mask)

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
        self.piano_view.set_colormap(name)
        if hasattr(self, 'polygon_window') and self.polygon_window:
            self.polygon_window.set_colormap(name)

    def change_tuning(self, name):
        tuning = self.preset_selector.get_tuning(name)
        if tuning:
            self.instrument_model.set_tuning(tuning)

    def closeEvent(self, event):
        self.sound_engine.stop()
        super().closeEvent(event)
