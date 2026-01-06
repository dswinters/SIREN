from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy,
                               QPushButton, QLabel, QComboBox, QStackedWidget,
                               QCheckBox, QLineEdit)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIntValidator
from models import InstrumentModel, ScaleModel
from modules.sound import SoundEngine
from controls import PresetSelector, OffsetController, ColormapDropdown
from controls.scale_dropdown import ScaleSelectDropdown
from .fretboard import FretboardView, FretlessView
from .scale_selector import ScaleSelectorView
from .piano import PianoView
from .polygon import PolygonView
from .tonnetz import TonnetzView
from .common import NOTE_NAMES
from .key_signature import KeySignatureView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SIREN")
        self.resize(2200, 400)

        self._init_models()
        self._init_ui()
        self._setup_layout()
        self._connect_signals()
        
        # Initialize label
        self.on_scale_updated()

    def _init_models(self):
        self.instrument_model = InstrumentModel()
        self.scale_model = ScaleModel()
        self.sound_engine = SoundEngine()

    def _init_ui(self):
        # Views
        self.fret_view = FretboardView(self.instrument_model, self.scale_model)
        self.fretless_view = FretlessView(self.instrument_model, self.scale_model)
        self.piano_view = PianoView(self.scale_model)
        self.scale_view = ScaleSelectorView(self.scale_model)
        self.key_signature_view = KeySignatureView(self.scale_model)
        
        self.lbl_scale_name = QLabel("")
        self.lbl_scale_name.setAlignment(Qt.AlignCenter)
        self.lbl_scale_name.setStyleSheet("font-size: 14px; font-weight: bold; color: #CCCCCC; padding: 5px;")

        # --- CONTROLS ---

        # 1. Visualization Controls
        self.btn_toggle_view = QPushButton("Fretless")
        self.colormap_selector = ColormapDropdown()
        self.btn_polygon = QPushButton("Polygon")
        self.btn_tonnetz = QPushButton("Tonnetz")

        # 2. Instrument Controls
        self.preset_selector = PresetSelector()
        self.preset_selector.insertItem(0, "Select Tuning")
        self.preset_selector.setCurrentIndex(0)
        
        self.offset_controller = OffsetController(self.instrument_model)

        # 3. Scale & Mode Controls
        self.scale_dropdown = ScaleSelectDropdown(self.scale_model)

        self.btn_left = QPushButton("<")
        self.btn_right = QPushButton(">")
        self.btn_trans_left = QPushButton("<")
        self.btn_trans_right = QPushButton(">")
        
        for b in [self.btn_left, self.btn_right, self.btn_trans_left, self.btn_trans_right]:
            b.setFixedWidth(30)
            b.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.cmb_transpose_root = QComboBox()
        self.cmb_transpose_root.addItem("Note")
        self.cmb_transpose_root.addItems(NOTE_NAMES)

        # 4. Sound Controls
        self.cmb_instrument = QComboBox()
        self.cmb_instrument.addItem("Select Instrument")
        self.cmb_instrument.addItems(self.sound_engine.get_available_instruments())
        
        self.btn_play = QPushButton("Play")
        self.chk_loop = QCheckBox("Loop")

        self.btn_oct_down = QPushButton("-")
        self.btn_oct_up = QPushButton("+")
        for b in [self.btn_oct_down, self.btn_oct_up]:
            b.setFixedWidth(30)
            b.setStyleSheet("font-size: 10px; font-weight: bold;")
        
        self.txt_bpm = QLineEdit("120")
        self.txt_bpm.setFixedWidth(40)
        self.txt_bpm.setValidator(QIntValidator(1, 999))
        self.txt_bpm.setPlaceholderText("BPM")

    def _setup_layout(self):
        # Sidebar Container
        sidebar = QWidget()
        sidebar.setFixedWidth(260)
        sidebar.setStyleSheet("background-color: #1e1e1e; border-right: 1px solid #333;")
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setSpacing(8)
        sb_layout.setContentsMargins(15, 15, 15, 15)

        def add_section_label(text):
            lbl = QLabel(text)
            lbl.setStyleSheet("color: #888; font-weight: bold; font-size: 11px; letter-spacing: 1px;")
            sb_layout.addWidget(lbl)

        # Section 1: Visualization
        add_section_label("VIEW SETTINGS")
        
        row_theme = QHBoxLayout()
        row_theme.addWidget(QLabel("Color Theme:"))
        row_theme.addWidget(self.colormap_selector)
        sb_layout.addLayout(row_theme)
        
        row_views = QHBoxLayout()
        row_views.addWidget(self.btn_toggle_view)
        row_views.addWidget(self.btn_polygon)
        row_views.addWidget(self.btn_tonnetz)
        sb_layout.addLayout(row_views)
        
        sb_layout.addSpacing(10)

        # Section 2: Instrument
        add_section_label("INSTRUMENT CONFIG")
        row_inst = QHBoxLayout()
        row_inst.addWidget(self.preset_selector)
        row_inst.addWidget(self.offset_controller)
        sb_layout.addLayout(row_inst)
        
        sb_layout.addSpacing(10)

        # Section 3: Scale & Key
        add_section_label("SCALE & KEY")
        sb_layout.addWidget(self.scale_dropdown)
        
        # Mode Row
        row_mode = QHBoxLayout()
        row_mode.addWidget(QLabel("Mode Rotation:"))
        row_mode.addStretch()
        row_mode.addWidget(self.btn_left)
        row_mode.addWidget(self.btn_right)
        sb_layout.addLayout(row_mode)
        
        # Transpose Row
        row_trans = QHBoxLayout()
        row_trans.addWidget(QLabel("Transpose Key:"))
        row_trans.addStretch()
        row_trans.addWidget(self.cmb_transpose_root)
        row_trans.addWidget(self.btn_trans_left)
        row_trans.addWidget(self.btn_trans_right)
        sb_layout.addLayout(row_trans)
        
        sb_layout.addSpacing(10)

        # Section 4: Audio
        add_section_label("AUDIO ENGINE")
        sb_layout.addWidget(self.cmb_instrument)
        
        row_audio_params = QHBoxLayout()
        row_audio_params.addWidget(QLabel("BPM:"))
        row_audio_params.addWidget(self.txt_bpm)
        row_audio_params.addStretch()
        row_audio_params.addWidget(QLabel("Octave:"))
        row_audio_params.addWidget(self.btn_oct_down)
        row_audio_params.addWidget(self.btn_oct_up)
        sb_layout.addLayout(row_audio_params)
        
        row_play = QHBoxLayout()
        row_play.addWidget(self.btn_play)
        row_play.addWidget(self.chk_loop)
        sb_layout.addLayout(row_play)
        
        sb_layout.addStretch()

        # Right Content Area
        self.central_stack = QStackedWidget()
        self.central_stack.addWidget(self.fret_view)
        self.central_stack.addWidget(self.piano_view)
        self.central_stack.addWidget(self.fretless_view)
        
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.addWidget(self.central_stack)
        
        # Bottom Section: Key Signature | Scale Selector + Label
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(20, 0, 0, 0)
        bottom_layout.setSpacing(0)

        bottom_layout.addWidget(self.key_signature_view)

        scale_col_widget = QWidget()
        scale_col_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        scale_col_layout = QVBoxLayout(scale_col_widget)
        scale_col_layout.setContentsMargins(0, 0, 0, 0)
        scale_col_layout.setSpacing(0)
        scale_col_layout.addWidget(self.scale_view)
        scale_col_layout.addWidget(self.lbl_scale_name)

        bottom_layout.addWidget(scale_col_widget)
        right_layout.addWidget(bottom_widget)

        # Main Layout
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(sidebar)
        main_layout.addWidget(right_widget)
        
        self.setCentralWidget(main_widget)

    def _connect_signals(self):
        self.sound_engine.playback_stopped.connect(self.on_playback_stopped)
        self.scale_model.updated.connect(self.on_scale_updated)
        self.sound_engine.note_played.connect(self.scale_view.highlight_note)
        
        self.btn_toggle_view.clicked.connect(self.toggle_instrument_view)
        self.colormap_selector.currentIndexChanged.connect(self.on_colormap_changed)
        self.btn_polygon.clicked.connect(self.open_polygon_view)
        self.btn_tonnetz.clicked.connect(self.open_tonnetz_view)
        self.preset_selector.currentTextChanged.connect(self.change_tuning)
        self.btn_right.clicked.connect(lambda: self.rotate_modes(1))
        self.btn_left.clicked.connect(lambda: self.rotate_modes(-1))
        self.btn_trans_left.clicked.connect(lambda: self.scale_model.transpose(-1))
        self.btn_trans_right.clicked.connect(lambda: self.scale_model.transpose(1))
        self.cmb_transpose_root.currentIndexChanged.connect(self.on_transpose_root_changed)
        self.cmb_instrument.currentTextChanged.connect(self.on_instrument_changed)
        self.btn_play.clicked.connect(self.toggle_playback)
        self.chk_loop.toggled.connect(self.sound_engine.set_looping)
        self.btn_oct_down.clicked.connect(lambda: self.sound_engine.change_octave(-1))
        self.btn_oct_up.clicked.connect(lambda: self.sound_engine.change_octave(1))
        self.txt_bpm.textChanged.connect(self.sound_engine.set_bpm)

    def toggle_instrument_view(self):
        current = self.central_stack.currentIndex()
        if current == 0: # Fretboard -> Fretless
            self.central_stack.setCurrentIndex(2)
            self.btn_toggle_view.setText("Piano")
        elif current == 2: # Fretless -> Piano
            self.central_stack.setCurrentIndex(1)
            self.btn_toggle_view.setText("Fretboard")
        else: # Piano -> Fretboard
            self.central_stack.setCurrentIndex(0)
            self.btn_toggle_view.setText("Fretless")

    def toggle_playback(self):
        if self.sound_engine.is_playing:
            self.sound_engine.stop()
            self.btn_play.setText("Play")
        else:
            self.sound_engine.update_scale(self.scale_model.root_note, self.scale_model.value)
            self.sound_engine.play()
            self.btn_play.setText("Stop")

    @Slot()
    def on_playback_stopped(self):
        self.btn_play.setText("Play")

    def on_scale_updated(self):
        self.sound_engine.update_scale(self.scale_model.root_note, self.scale_model.value)
        
        # Update scale name label
        root_name = self.scale_model.note_names[self.scale_model.root_note]
        current_val = self.scale_model.value
        scale_name = None
        
        for i in range(self.scale_dropdown.count()):
            val = self.scale_dropdown.itemData(i)
            if val is not None and int(val) == current_val:
                scale_name = self.scale_dropdown.itemText(i).strip()
                break
        
        full_text = ""
        if scale_name:
            full_text = f"{root_name} {scale_name}"
            self.lbl_scale_name.setText(full_text)
        else:
            self.lbl_scale_name.setText("")
            
        if hasattr(self, 'polygon_window') and self.polygon_window.isVisible():
            self.polygon_window.set_scale_name(full_text)

    def rotate_modes(self, direction):
        if self.scale_view.is_animating():
            return
        if hasattr(self, 'polygon_window') and self.polygon_window.isVisible() and self.polygon_window.is_animating():
            return
        if hasattr(self, 'tonnetz_window') and self.tonnetz_window.isVisible() and self.tonnetz_window.is_animating():
            return
        self.scale_model.rotate_modes(direction)

    def open_polygon_view(self):
        if not hasattr(self, 'polygon_window') or not self.polygon_window.isVisible():
            self.polygon_window = PolygonView(self.scale_model)
            self.polygon_window.set_colormap(self.colormap_selector.itemData(self.colormap_selector.currentIndex()))
            self.polygon_window.set_scale_name(self.lbl_scale_name.text())
            self.sound_engine.note_played.connect(self.polygon_window.highlight_note)
            self.polygon_window.show()
        else:
            self.polygon_window.raise_()
            self.polygon_window.activateWindow()

    def open_tonnetz_view(self):
        if not hasattr(self, 'tonnetz_window') or not self.tonnetz_window.isVisible():
            self.tonnetz_window = TonnetzView(self.scale_model)
            self.tonnetz_window.set_colormap(self.colormap_selector.itemData(self.colormap_selector.currentIndex()))
            self.sound_engine.note_played.connect(self.tonnetz_window.highlight_note)
            self.tonnetz_window.show()
        else:
            self.tonnetz_window.raise_()
            self.tonnetz_window.activateWindow()

    def on_colormap_changed(self, index):
        name = self.colormap_selector.itemData(index)
        self.update_colormaps(name)

    def update_colormaps(self, name):
        self.fret_view.set_colormap(name)
        self.scale_view.set_colormap(name)
        self.fretless_view.set_colormap(name)
        self.piano_view.set_colormap(name)
        if hasattr(self, 'polygon_window') and self.polygon_window:
            self.polygon_window.set_colormap(name)
        if hasattr(self, 'tonnetz_window') and self.tonnetz_window:
            self.tonnetz_window.set_colormap(name)

    def change_tuning(self, name):
        if name == "Select Tuning": return
        tuning = self.preset_selector.get_tuning(name)
        if tuning:
            self.instrument_model.set_tuning(tuning)
        self.preset_selector.blockSignals(True)
        self.preset_selector.setCurrentIndex(0)
        self.preset_selector.blockSignals(False)

    def on_instrument_changed(self, name):
        if name == "Select Instrument": return
        self.sound_engine.set_instrument(name)
        self.cmb_instrument.blockSignals(True)
        self.cmb_instrument.setCurrentIndex(0)
        self.cmb_instrument.blockSignals(False)

    def on_transpose_root_changed(self, index):
        if index <= 0: return
        note_val = index - 1
        self.scale_model.set_root_note(note_val)
        self.cmb_transpose_root.blockSignals(True)
        self.cmb_transpose_root.setCurrentIndex(0)
        self.cmb_transpose_root.blockSignals(False)

    def closeEvent(self, event):
        self.sound_engine.stop()
        if hasattr(self, 'polygon_window') and self.polygon_window:
            self.polygon_window.close()
        if hasattr(self, 'tonnetz_window') and self.tonnetz_window:
            self.tonnetz_window.close()
        super().closeEvent(event)
