import numpy as np
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtGui import QPainter, QFont, QColor, QPen
from PySide6.QtCore import Qt, QPointF, QRectF
from .base_view import BaseNoteView
from .mixins import RotationAnimationMixin, PlaybackHighlightMixin
from .common import INACTIVE_OPACITY
from modules.chords import compute_chords, TRIADS
from modules.math import pitch_set

class ScaleSelectorView(BaseNoteView, RotationAnimationMixin, PlaybackHighlightMixin):
    def __init__(self, scale_model, spelling):
        super().__init__(scale_model, spelling)
        
        self.setFixedHeight(100)
        self.setStyleSheet("background-color: #121212;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Initialize animation from Mixin
        self.init_animation()
        self.init_highlight_animation()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        num_cells = 12
        margin = 5
        available_w = w - (2 * margin)
        cell_w = available_w / num_cells
        
        painter.setFont(QFont("Arial", 10, QFont.Bold))

        # Precompute chords for the current scale
        chord_map = {}
        scale_num = self.scale_model.number
        root_note = self.scale_model.root_note
        
        active_notes = pitch_set(scale_num)
        chords_per_degree = compute_chords(scale_num)
        
        for note_val, shapes in zip(active_notes, chords_per_degree):
            names = []
            interval = (note_val - root_note) % 12
            for shape in shapes:
                if shape in TRIADS:
                    names.append(TRIADS[shape](interval))
            if names:
                chord_map[note_val] = names

        # We want to render cells based on the animated offset.
        # If offset increases (e.g. 0 -> 1), the "start" index moves up.
        # This effectively shifts notes to the Left.
        # If offset decreases (e.g. 0 -> 11), notes shift Right.
        
        # To handle smooth wrapping, we render from k = -1 to 13
        # and calculate position relative to the floating offset.
        
        start_k = int(np.floor(self._anim_offset)) - 1
        end_k = int(np.ceil(self._anim_offset + 12)) + 1

        text_space = 40
        avail_h = h - text_space

        for k in range(start_k, end_k):
            # Calculate Screen X
            # Position 0 is at (0 - offset) * width
            pos_index = k - self._anim_offset
            
            # Skip if clearly offscreen
            if pos_index < -1 or pos_index > 12:
                continue

            cx = margin + (pos_index * cell_w) + (cell_w / 2)
            cy = avail_h / 2
            
            # Determine Note
            note_val = k % 12
            
            radius = min(cell_w, avail_h) / 2 - 4
            
            is_active = (self.scale_model.number >> note_val) & 1
            is_root = (note_val == self.scale_model.root_note)
            
            active_pen = None
            if is_active:
                base_pen = QColor("white") if is_root else QColor("#929292")
                pen_color = self.get_interpolated_color(note_val, base_pen, QColor("#409C40"))
                active_pen = QPen(pen_color, 4)

            self.draw_note_label(painter, QPointF(cx, cy), radius, note_val, is_active, is_root, 
                                 font_size=10, active_pen=active_pen, offset_override=self._anim_offset)

            # Draw chord labels
            if is_active and note_val in chord_map:
                labels = chord_map[note_val]
                label_y = cy + radius + 15
                painter.setFont(QFont("Arial", 9))
                painter.setPen(QColor("#CCCCCC"))
                for label in labels:
                    painter.drawText(QRectF(cx - 30, label_y, 60, 12), Qt.AlignCenter, label)
                    label_y += 12

    def mousePressEvent(self, event):
        w = self.width()
        margin = 5
        available_w = w - (2 * margin)
        
        # Guard against zero-width (though unlikely in this layout)
        if available_w <= 0: return

        cell_w = available_w / 12
        x = event.position().x()
        
        # Calculate the visual index (0.0 to 12.0)
        visual_pos = (x - margin) / cell_w
        
        # The note 'k' is drawn at center: k - offset + 0.5
        # We want to find the k that minimizes distance to visual_pos.
        # equation: visual_pos = k - offset + 0.5
        # therefore: k = visual_pos + offset - 0.5
        
        clicked_val = int(round(visual_pos + self._anim_offset - 0.5)) % 12
        
        if event.button() == Qt.LeftButton:
            self.scale_model.toggle_note_active(clicked_val)
        elif event.button() == Qt.RightButton:
            if not self.is_animating():
                if clicked_val == self.scale_model.root_note:
                    self.spelling.toggle_enharmonic_spelling()
                else:
                    self.scale_model.set_root_note(clicked_val)

    def wheelEvent(self, event):
        if self.is_animating():
            return
        
        delta = event.angleDelta().y()
        steps = 0
        if delta > 0: steps = -1
        elif delta < 0: steps = 1
        
        if steps == 0: return

        if event.modifiers() & Qt.ShiftModifier:
            self.scale_model.transpose(steps)
        else:
            self.scale_model.rotate_modes(steps)
