import math
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QFont, QColor, QPen, QPolygonF, QConicalGradient, QPainterPath
from PySide6.QtCore import Qt, QPointF, QRectF, QPropertyAnimation, Property, QEasingCurve
from .base_view import BaseNoteView
from .common import NOTE_NAMES, INACTIVE_OPACITY

class PolygonView(BaseNoteView):
    def __init__(self, scale_model):
        super().__init__(scale_model)
        self.scale_model.updated.connect(self.on_model_update)
        self.setWindowTitle("Polygon View")
        self.resize(400, 400)
        self.setStyleSheet("background-color: #121212;")

        # Animation State
        self._anim_offset = float(self.scale_model.rotation_offset)
        
        self.anim = QPropertyAnimation(self, b"animOffset")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

    def is_animating(self):
        return self.anim.state() == QPropertyAnimation.State.Running

    def get_anim_offset(self):
        return self._anim_offset

    def set_anim_offset(self, val):
        self._anim_offset = val
        self.update()

    animOffset = Property(float, get_anim_offset, set_anim_offset)

    def on_model_update(self):
        target = self.scale_model.rotation_offset
        current = self._anim_offset
        
        diff = target - current
        
        if diff > 6:
            self._anim_offset += 12
        elif diff < -6:
            self._anim_offset -= 12
            
        self.anim.setStartValue(self._anim_offset)
        self.anim.setEndValue(target)
        self.anim.start()
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
                
                active_low = 1.0 if idx_low in self.scale_model.active_notes else 0.0
                active_high = 1.0 if idx_high in self.scale_model.active_notes else 0.0
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
        active_points = []
        
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
            
            if i in self.scale_model.active_notes:
                active_points.append(p)

        # Draw polygon connecting active notes
        if len(active_points) > 1:
            painter.setPen(QPen(QColor("white"), 4))
            painter.setBrush(QColor(255, 255, 255, 30))
            painter.drawPolygon(QPolygonF(active_points))
            
        # Draw notes
        note_radius = 15
        for i in range(12):
            pos = note_positions[i]
            is_active = i in self.scale_model.active_notes
            bg_color = self.get_color_for_note(i, offset_override=offset)
            
            if is_active:
                painter.setPen(QPen(QColor("white"), 2))
            else:
                painter.setPen(Qt.NoPen)
            
            painter.setBrush(bg_color)
            painter.drawEllipse(pos, note_radius, note_radius)
            
            text_color = QColor("black") if bg_color.lightness() > 128 else QColor("white")
            if not is_active:
                text_color.setAlphaF(INACTIVE_OPACITY)
                
            painter.setPen(text_color)
            rect = QRectF(pos.x() - note_radius, pos.y() - note_radius, note_radius*2, note_radius*2)
            painter.drawText(rect, Qt.AlignCenter, NOTE_NAMES[i])

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
                        self.scale_model.set_rotation_offset(i)
                return

    def wheelEvent(self, event):
        if self.is_animating():
            return
        delta = event.angleDelta().y()
        if delta > 0:
            self.scale_model.rotate_view(-1)
        elif delta < 0:
            self.scale_model.rotate_view(1)