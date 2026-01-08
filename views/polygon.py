import math
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QFont, QColor, QPen, QPolygonF, QConicalGradient, QPainterPath
from PySide6.QtCore import Qt, QPointF, QRectF
from .base_view import BaseNoteView
from .mixins import RotationAnimationMixin, PlaybackHighlightMixin
from .common import INACTIVE_OPACITY, ACTIVE_EDGE_COLOR, ACTIVE_EDGE_WIDTH

class PolygonView(BaseNoteView, RotationAnimationMixin, PlaybackHighlightMixin):
    def __init__(self, scale_model):
        super().__init__(scale_model)
        self.setWindowTitle("Polygon View")
        self.resize(400, 400)
        self.setStyleSheet("background-color: #121212;")
        self._last_value = self.scale_model.value
        self._static_polygon = False
        self._scale_name_text = ""

        # Initialize animation from Mixin
        self.init_animation()
        self.init_highlight_animation()

    def on_model_update(self):
        new_value = self.scale_model.value
        target = self.scale_model.root_note
        
        # If value is unchanged but offset changed, it's a transpose -> static polygon
        if new_value == self._last_value and target != self._anim_offset:
            self._static_polygon = True
        else:
            self._static_polygon = False
            
        self._last_value = new_value
        RotationAnimationMixin.on_model_update(self)

    def set_scale_name(self, text):
        self._scale_name_text = text
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        radius = min(w, h) / 2 - 40
        
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        
        # Draw Annulus
        if self.cmap:
            annulus_width = 40
            half_width = annulus_width / 2
            r_in = radius - half_width
            r_out = radius + half_width
            
            path = QPainterPath()
            path.addEllipse(QPointF(cx, cy), r_out, r_out)
            path.addEllipse(QPointF(cx, cy), r_in, r_in)
            path.setFillRule(Qt.OddEvenFill)
            
            gradient = QConicalGradient(QPointF(cx, cy), 90)
            
            steps = 360
            
            for i in range(steps + 1):
                s = i / steps
                t = (1.0 - s) % 1.0
                
                angle_deg = t * 360.0
                
                note_pos = self._anim_offset + (angle_deg / 30.0)
                idx_low = int(math.floor(note_pos)) % 12
                idx_high = (idx_low + 1) % 12
                ratio = note_pos - math.floor(note_pos)
                
                active_low = 1.0 if (self.scale_model.pitch_set >> idx_low) & 1 else 0.0
                active_high = 1.0 if (self.scale_model.pitch_set >> idx_high) & 1 else 0.0
                opacity = ((1.0 - ratio) * active_low + ratio * active_high) ** 2.0
                
                rgba = self.cmap(t)
                c = QColor.fromRgbF(rgba[0], rgba[1], rgba[2], (rgba[3] if len(rgba) > 3 else 1.0) * opacity)
                gradient.setColorAt(s, c)
                
            painter.setBrush(gradient)
            painter.setPen(Qt.NoPen)
            painter.drawPath(path)

        # Calculate positions
        offset = self._anim_offset
        note_positions = {}
        
        for i in range(12):
            # -90 degrees is top. 
            # We want note 'offset' at top.
            # So angle for note i is -90 + (i - offset) * 30
            angle_deg = -90 + (i - offset) * 30
            angle_rad = math.radians(angle_deg)
            
            nx = cx + radius * math.cos(angle_rad)
            ny = cy + radius * math.sin(angle_rad)
            p = QPointF(nx, ny)
            note_positions[i] = p
            
        # Calculate polygon points
        # Use target offset for static polygon (Transpose), anim offset otherwise (Rotate)
        poly_offset = self.scale_model.root_note if self._static_polygon else self._anim_offset
        active_points = []
        
        for i in range(12):
            if (self.scale_model.pitch_set >> i) & 1:
                angle_deg = -90 + (i - poly_offset) * 30
                angle_rad = math.radians(angle_deg)
                px = cx + radius * math.cos(angle_rad)
                py = cy + radius * math.sin(angle_rad)
                active_points.append(QPointF(px, py))

        # Draw polygon connecting active notes
        if len(active_points) > 1:
            painter.setPen(QPen(QColor(ACTIVE_EDGE_COLOR), ACTIVE_EDGE_WIDTH))
            painter.setBrush(QColor(255, 255, 255, 30))
            painter.drawPolygon(QPolygonF(active_points))
            
        # Draw notes
        note_radius = 15
        for i in range(12):
            pos = note_positions[i]
            is_active = (self.scale_model.pitch_set >> i) & 1
            is_root = (i == self.scale_model.root_note)
            
            active_pen = None
            if is_active:
                base_pen = QColor("white")
                pen_color = self.get_interpolated_color(i, base_pen, QColor("#409C40"))
                active_pen = QPen(pen_color, 2)

            self.draw_note_label(painter, pos, note_radius, i, is_active, is_root, 
                                 font_size=10, active_pen=active_pen, offset_override=offset)

        # Draw Scale Name in Center
        if self._scale_name_text:
            painter.setPen(QColor("#CCCCCC"))
            painter.setFont(QFont("Arial", 16, QFont.Bold))
            painter.drawText(self.rect(), Qt.AlignCenter, self._scale_name_text)

    def mousePressEvent(self, event):
        click_pos = event.position()
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        radius = min(w, h) / 2 - 40
        offset = self._anim_offset
        
        for i in range(12):
            angle_deg = -90 + (i - offset) * 30
            angle_rad = math.radians(angle_deg)
            nx = cx + radius * math.cos(angle_rad)
            ny = cy + radius * math.sin(angle_rad)
            
            if math.hypot(click_pos.x() - nx, click_pos.y() - ny) < 20:
                if event.button() == Qt.LeftButton:
                    self.scale_model.toggle_note_active(i)
                elif event.button() == Qt.RightButton:
                    if not self.is_animating():
                        self.scale_model.set_root_note(i)
                return

    def wheelEvent(self, event):
        if self.is_animating():
            return
        
        delta = event.angleDelta().y()
        steps = 0
        if delta > 0:
            steps = -1
        elif delta < 0:
            steps = 1
            
        if steps == 0: return

        if event.modifiers() & Qt.ShiftModifier:
            self.scale_model.transpose(steps)
        else:
            self.scale_model.rotate_modes(steps)