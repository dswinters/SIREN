from PySide6.QtWidgets import QSizePolicy
from PySide6.QtGui import QPainter, QPen, QColor, QFont
from PySide6.QtCore import Qt, QRectF, QPointF
from .base_view import BaseNoteView
from .common import FONT_SIZE, INACTIVE_OPACITY

class PianoView(BaseNoteView):
    def __init__(self, scale_model, octaves=3):
        super().__init__(scale_model)
        self.octaves = octaves
        self.scale_model.updated.connect(self.update)
        self.setStyleSheet("background-color: #121212;")
        self.setMinimumHeight(300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Key definitions
        self.white_indices = [0, 2, 4, 5, 7, 9, 11]
        self.black_indices = [1, 3, 6, 8, 10]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # Geometry
        white_keys_per_octave = 7
        total_white_keys = self.octaves * white_keys_per_octave
        key_w = w / total_white_keys
        black_key_w = key_w * 0.6
        black_key_h = h * 0.6
        
        self.white_keys = []
        self.black_keys = []
        
        # Calculate key rectangles
        for oct_idx in range(self.octaves):
            octave_offset_x = oct_idx * white_keys_per_octave * key_w
            
            for i in range(12):
                note_val = i
                
                if i in self.white_indices:
                    w_idx = self.white_indices.index(i)
                    x = octave_offset_x + (w_idx * key_w)
                    rect = QRectF(x, 0, key_w, h)
                    self.white_keys.append((rect, note_val))
                else:
                    # Black keys are centered on the boundary of white keys
                    # C#(1) -> between 0 and 1
                    # D#(3) -> between 1 and 2
                    # F#(6) -> between 3 and 4
                    # G#(8) -> between 4 and 5
                    # A#(10) -> between 5 and 6
                    
                    # Map note index to the white key index to its left
                    if i == 1: w_ref = 0
                    elif i == 3: w_ref = 1
                    elif i == 6: w_ref = 3
                    elif i == 8: w_ref = 4
                    elif i == 10: w_ref = 5
                    
                    x = octave_offset_x + (w_ref * key_w) + key_w - (black_key_w / 2)
                    rect = QRectF(x, 0, black_key_w, black_key_h)
                    self.black_keys.append((rect, note_val))

        # Draw Keys (White then Black)
        painter.setPen(QPen(QColor("black"), 1))
        
        for rect, _ in self.white_keys:
            painter.setBrush(QColor("white"))
            painter.drawRect(rect)
            
        for rect, _ in self.black_keys:
            painter.setBrush(QColor("black"))
            painter.drawRect(rect)
            
        # Draw Labels (White then Black to ensure visibility)
        for rect, note_val in self.white_keys:
            self._draw_label(painter, rect, note_val)
            
        for rect, note_val in self.black_keys:
            self._draw_label(painter, rect, note_val)

    def _draw_label(self, painter, key_rect, note_val):
        radius = 11
        cx = key_rect.center().x()
        cy = key_rect.bottom() - radius - 8
        
        bg_color = self.get_color_for_note(note_val)
        is_active = (self.scale_model.active_notes >> note_val) & 1
        
        if is_active:
            painter.setPen(QPen(QColor("#929292"), 2))
        else:
            painter.setPen(Qt.NoPen)
            
        painter.setBrush(bg_color)
        painter.drawEllipse(QPointF(cx, cy), radius, radius)
        
        text_color = QColor("black") if bg_color.lightness() > 128 else QColor("white")
        if not is_active:
            text_color.setAlphaF(INACTIVE_OPACITY)
            
        painter.setPen(text_color)
        painter.setFont(QFont("Arial", FONT_SIZE, QFont.Bold))
        rect = QRectF(cx - radius, cy - radius, radius*2, radius*2)
        painter.drawText(rect, Qt.AlignCenter, self.scale_model.note_names[note_val])

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position()
            # Check black keys first (z-order top)
            for rect, note_val in self.black_keys + self.white_keys:
                if rect.contains(pos):
                    self.scale_model.toggle_note_active(note_val)
                    return