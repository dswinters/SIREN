import numpy as np
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtGui import QPainter, QFont, QColor, QPen
from PySide6.QtCore import Qt, QPointF, QRectF
from .base_view import BaseNoteView
from .mixins import RotationAnimationMixin, PlaybackHighlightMixin
from .common import INACTIVE_OPACITY

class ScaleSelectorView(BaseNoteView, RotationAnimationMixin, PlaybackHighlightMixin):
    def __init__(self, scale_model):
        super().__init__(scale_model)
        
        self.setFixedHeight(60)
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

        # We want to render cells based on the animated offset.
        # If offset increases (e.g. 0 -> 1), the "start" index moves up.
        # This effectively shifts notes to the Left.
        # If offset decreases (e.g. 0 -> 11), notes shift Right.
        
        # To handle smooth wrapping, we render from k = -1 to 13
        # and calculate position relative to the floating offset.
        
        start_k = int(np.floor(self._anim_offset)) - 1
        end_k = int(np.ceil(self._anim_offset + 12)) + 1

        for k in range(start_k, end_k):
            # Calculate Screen X
            # Position 0 is at (0 - offset) * width
            pos_index = k - self._anim_offset
            
            # Skip if clearly offscreen
            if pos_index < -1 or pos_index > 12:
                continue

            cx = margin + (pos_index * cell_w) + (cell_w / 2)
            cy = h / 2
            
            # Determine Note
            note_val = k % 12
            
            radius = min(cell_w, h) / 2 - 4
            
            # Pass the animated offset to get_color so colors shift smoothly too
            bg_color = self.get_color_for_note(note_val, offset_override=self._anim_offset)
            is_active = (self.scale_model.active_notes >> note_val) & 1
            
            if is_active:
                base_pen = QColor("#929292")
                pen_color = self.get_interpolated_color(note_val, base_pen, QColor("#409C40"))
                painter.setPen(QPen(pen_color, 4))
            else:
                painter.setPen(Qt.NoPen)
            painter.setBrush(bg_color)
            painter.drawEllipse(QPointF(cx, cy), radius, radius)
            
            text_color = QColor("black") if bg_color.lightness() > 128 else QColor("white")
            if not is_active:
                text_color.setAlphaF(INACTIVE_OPACITY)
                
            painter.setPen(text_color)
            rect = QRectF(cx - radius, cy - radius, radius*2, radius*2)
            painter.drawText(rect, Qt.AlignCenter, self.scale_model.note_names[note_val])

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
                    self.scale_model.toggle_naming_convention()
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
