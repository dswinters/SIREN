import numpy as np
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtGui import QPainter, QFont, QColor, QPen
from PySide6.QtCore import Qt, QPropertyAnimation, Property, QEasingCurve, QPointF, QRectF
from .base_view import BaseNoteView
from .common import NOTE_NAMES, INACTIVE_OPACITY

class ScaleSelectorView(BaseNoteView):
    def __init__(self, scale_model):
        super().__init__(scale_model)
        self.scale_model.updated.connect(self.on_model_update)
        
        self.setFixedHeight(60)
        self.setStyleSheet("background-color: #121212;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Animation State
        self._anim_offset = float(self.scale_model.rotation_offset)
        
        self.anim = QPropertyAnimation(self, b"animOffset")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

    def is_animating(self):
        return self.anim.state() == QPropertyAnimation.State.Running

    # Define the property for the animation framework
    def get_anim_offset(self):
        return self._anim_offset

    def set_anim_offset(self, val):
        self._anim_offset = val
        self.update() # Trigger repaint on every frame

    animOffset = Property(float, get_anim_offset, set_anim_offset)

    def on_model_update(self):
        target = self.scale_model.rotation_offset
        current = self._anim_offset
        
        # Calculate shortest path for circular wrapping (0 <-> 11)
        diff = (target - current)
        
        # If diff is > 6, it means we went the "long way" around the circle
        # e.g., jumping from 0 to 11 (diff = 11). We want -1.
        # e.g., jumping from 11 to 0 (diff = -11). We want +1.
        
        # Normalize current to be close to target for animation purposes
        # We temporarily set current to a value that makes the math work, 
        # then animate to the integer target.
        if diff > 6:
            self._anim_offset += 12
        elif diff < -6:
            self._anim_offset -= 12
            
        self.anim.setStartValue(self._anim_offset)
        self.anim.setEndValue(target)
        self.anim.start()
        
        # Also repaint in case only active status changed (no motion)
        self.update()

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
            is_active = note_val in self.scale_model.active_notes
            
            if is_active:
                painter.setPen(QPen(QColor("#929292"), 4))
            else:
                painter.setPen(Qt.NoPen)
            painter.setBrush(bg_color)
            painter.drawEllipse(QPointF(cx, cy), radius, radius)
            
            text_color = QColor("black") if bg_color.lightness() > 128 else QColor("white")
            if not is_active:
                text_color.setAlphaF(INACTIVE_OPACITY)
                
            painter.setPen(text_color)
            rect = QRectF(cx - radius, cy - radius, radius*2, radius*2)
            painter.drawText(rect, Qt.AlignCenter, NOTE_NAMES[note_val])

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
                self.scale_model.set_rotation_offset(clicked_val)
