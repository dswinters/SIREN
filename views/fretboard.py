import numpy as np
from PySide6.QtWidgets import QSizePolicy, QMenu
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QAction
from PySide6.QtCore import Qt, QLineF, QPointF, QRectF
from .base_view import BaseNoteView
from .common import NOTE_NAMES, FONT_SIZE, INACTIVE_OPACITY, SINGLE_MARKERS, DOUBLE_MARKERS

class FretboardView(BaseNoteView):
    def __init__(self, model):
        super().__init__(model)
        self.model.updated.connect(self.update) # Standard update
        self.setStyleSheet("background-color: #121212;")
        self.setMinimumHeight(300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def get_geometry(self):
        w, h = self.width(), self.height()
        margin_x = 60
        margin_top = 30
        margin_bottom = 50 
        n = np.arange(self.model.num_frets + 1)
        scale_length = (w - 2 * margin_x) / 0.75
        fret_xs = (scale_length * (1 - 2**(-n/12))) + margin_x
        
        if self.model.num_strings == 1:
            string_ys = np.array([h / 2])
        else:
            string_ys = np.linspace(h - margin_bottom, margin_top, self.model.num_strings)
        return fret_xs, string_ys, margin_x, margin_bottom

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        fret_xs, string_ys, margin_x, margin_bottom = self.get_geometry()
        margin_top = 30 

        # Grid
        painter.setPen(QPen(QColor("#555555"), 2))
        for y in string_ys: painter.drawLine(QLineF(margin_x, y, w - margin_x, y))
        painter.setPen(QPen(QColor("#AAAAAA"), 2))
        fret_bot_y = h - margin_bottom
        for x in fret_xs: painter.drawLine(QLineF(x, margin_top, x, fret_bot_y))
        if len(fret_xs) > 0:
            painter.setPen(QPen(QColor("#FFFFFF"), 5))
            painter.drawLine(QLineF(fret_xs[0], margin_top, fret_xs[0], fret_bot_y))

        # Markers
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#FFFFFF"))
        marker_y = h - (margin_bottom / 2)
        def get_cx(f): return (fret_xs[f-1]+fret_xs[f])/2 if f <= self.model.num_frets else None
        
        for f in SINGLE_MARKERS:
            cx = get_cx(f)
            if cx: painter.drawEllipse(QPointF(cx, marker_y), 3, 3)
        for f in DOUBLE_MARKERS:
            cx = get_cx(f)
            if cx:
                painter.drawEllipse(QPointF(cx-6, marker_y), 3, 3)
                painter.drawEllipse(QPointF(cx+6, marker_y), 3, 3)

        # Notes
        grid = self.model.get_note_grid()
        painter.setFont(QFont("Arial", FONT_SIZE, QFont.Bold))
        radius = 11
        
        for s_idx, y in enumerate(string_ys):
            for f_idx, x in enumerate(fret_xs):
                note_val = grid[s_idx, f_idx]
                
                if f_idx == 0: text_x = x - 30 
                else: text_x = (fret_xs[f_idx - 1] + x) / 2

                bg_color = self.get_color_for_note(note_val)
                is_active = note_val in self.model.active_notes
                
                painter.setPen(Qt.NoPen)
                painter.setBrush(bg_color)
                painter.drawEllipse(QPointF(text_x, y), radius, radius)
                
                text_color = QColor("black") if bg_color.lightness() > 128 else QColor("white")
                if not is_active: text_color.setAlphaF(INACTIVE_OPACITY)
                
                painter.setPen(text_color)
                rect = QRectF(text_x - radius, y - radius, radius*2, radius*2)
                painter.drawText(rect, Qt.AlignCenter, NOTE_NAMES[note_val])

    def mousePressEvent(self, event):
        fret_xs, string_ys, _, _ = self.get_geometry()
        click_pos = event.position()
        grid = self.model.get_note_grid()
        
        for s_idx, y in enumerate(string_ys):
            for f_idx, x in enumerate(fret_xs):
                cx = (x - 30) if f_idx == 0 else (fret_xs[f_idx - 1] + x) / 2
                if np.sqrt((click_pos.x()-cx)**2 + (click_pos.y()-y)**2) < 15:
                    if event.button() == Qt.LeftButton:
                        self.model.toggle_note_active(grid[s_idx, f_idx])
                    elif event.button() == Qt.RightButton and f_idx == 0:
                        self.show_tuning_menu(s_idx, event.globalPosition().toPoint())
                    return

    def show_tuning_menu(self, string_idx, global_pos):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #333; color: white; }")
        for i, name in enumerate(NOTE_NAMES):
            action = QAction(name, self)
            action.triggered.connect(lambda c, v=i: self.model.set_string_note(string_idx, v))
            menu.addAction(action)
        menu.exec(global_pos)
