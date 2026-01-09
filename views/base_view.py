from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QColor, QPainter, QFont, QPen
from PySide6.QtCore import Qt, QRectF
from .common import CYCLIC_MAPS, INACTIVE_OPACITY, get_cmap

class BaseNoteView(QWidget):
    def __init__(self, scale_model):
        super().__init__()
        self.scale_model = scale_model
        # Base class does NOT connect update automatically to avoid double paints in animated views
        
        self.current_cmap_name = CYCLIC_MAPS[0] if CYCLIC_MAPS else None
        self.cmap = None
        self._update_cmap()

    def set_colormap(self, name):
        self.current_cmap_name = name
        self._update_cmap()
        self.update()

    def _update_cmap(self):
        if self.current_cmap_name:
            self.cmap = get_cmap(self.current_cmap_name)

    def get_color_for_note(self, note_val, offset_override=None):
        if not self.cmap: return QColor("#333333")
        
        is_active = (self.scale_model.pitch_set >> note_val) & 1
        if is_active:
            # Use override if provided (for smooth color transitions during animation)
            # otherwise use model state
            offset = offset_override if offset_override is not None else self.scale_model.root_note
            
            relative_val = (note_val - offset) % 12
            norm_val = relative_val / 12.0
            r, g, b, a = self.cmap(norm_val) 
            return QColor.fromRgbF(r, g, b, a)
        else:
            return QColor.fromRgbF(0.6, 0.6, 0.6, INACTIVE_OPACITY)

    def draw_note_label(self, painter, center, radius, note_val, is_active, is_root, font_size=10, opacity=1.0, active_pen=None, offset_override=None, inactive_text_opacity=None, inactive_text_color=None):
        bg_color = self.get_color_for_note(note_val, offset_override=offset_override)
        
        # Apply opacity to background
        if opacity < 1.0:
            bg_color.setAlphaF(bg_color.alphaF() * opacity)

        # Draw Background
        painter.setBrush(bg_color)
        
        # Determine outline for standard active notes (non-root)
        if is_active and not is_root and active_pen:
            pen = QPen(active_pen)
            if opacity < 1.0:
                c = pen.color()
                c.setAlphaF(c.alphaF() * opacity)
                pen.setColor(c)
            painter.setPen(pen)
        else:
            painter.setPen(Qt.NoPen)
            
        painter.drawEllipse(center, radius, radius)

        # Root Note Styling
        if is_active and is_root:
            # Outer White (Thick)
            white_color = QColor("white")
            white_color.setAlphaF(white_color.alphaF() * opacity)
            painter.setPen(QPen(white_color, 6))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(center, radius, radius)
            
            # Inner Colored (Thin, Inset)
            inner_color = QColor("white")
            if self.cmap:
                r, g, b, a = self.cmap(0.0)
                inner_color = QColor.fromRgbF(r, g, b, a)
            inner_color.setAlphaF(inner_color.alphaF() * opacity)
            
            painter.setPen(QPen(inner_color, 3))
            painter.drawEllipse(center, radius, radius)

        # Draw Text
        if not is_active and inactive_text_color:
            text_color = QColor(inactive_text_color)
        else:
            text_color = QColor("black") if bg_color.lightness() > 128 else QColor("white")
        text_opacity = opacity
        if not is_active:
            text_opacity *= (inactive_text_opacity if inactive_text_opacity is not None else INACTIVE_OPACITY)
        
        text_color.setAlphaF(text_color.alphaF() * text_opacity)
        
        painter.setPen(text_color)
        painter.setFont(QFont("Arial", font_size, QFont.Bold))
        rect = QRectF(center.x() - radius, center.y() - radius, radius*2, radius*2)
        painter.drawText(rect, Qt.AlignCenter, self.scale_model.note_names[note_val])
