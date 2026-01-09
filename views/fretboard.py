import numpy as np
from PySide6.QtWidgets import QSizePolicy, QMenu
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QAction
from PySide6.QtCore import Qt, QLineF, QPointF, QRectF
from .base_view import BaseNoteView
from .common import FONT_SIZE, INACTIVE_OPACITY, SINGLE_MARKERS, DOUBLE_MARKERS

class FingerboardView(BaseNoteView):
    MARGIN_X = 60
    MARGIN_TOP = 30
    MARGIN_BOTTOM = 50

    def __init__(self, instrument_model, scale_model):
        super().__init__(scale_model)
        self.instrument_model = instrument_model
        self.instrument_model.updated.connect(self.update)
        self.scale_model.updated.connect(self.update)
        self.setStyleSheet("background-color: #121212;")
        self.setMinimumHeight(300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def get_geometry(self):
        w, h = self.width(), self.height()
        n = np.arange(self.instrument_model.num_frets + 1)
        scale_length = (w - 2 * self.MARGIN_X) / 0.75
        fret_xs = (scale_length * (1 - 2**(-n/12))) + self.MARGIN_X
        
        if self.instrument_model.num_strings == 1:
            string_ys = np.array([h / 2])
        else:
            string_ys = np.linspace(h - self.MARGIN_BOTTOM, self.MARGIN_TOP, self.instrument_model.num_strings)
        return fret_xs, string_ys

    def get_note_center(self, f_idx, x, prev_x):
        raise NotImplementedError

    def draw_markers(self, painter, fret_xs, marker_y):
        pass

    def get_fret_line_pen(self):
        return QPen(QColor("#AAAAAA"), 2)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        fret_xs, string_ys = self.get_geometry()

        # Grid
        painter.setPen(QPen(QColor("#555555"), 4))
        for y in string_ys: painter.drawLine(QLineF(self.MARGIN_X, y, w - self.MARGIN_X, y))
        
        painter.setPen(self.get_fret_line_pen())
        fret_bot_y = h - self.MARGIN_BOTTOM
        for x in fret_xs: painter.drawLine(QLineF(x, self.MARGIN_TOP, x, fret_bot_y))
        
        # Nut
        if len(fret_xs) > 0:
            painter.setPen(QPen(QColor("#FFFFFF"), 5))
            painter.drawLine(QLineF(fret_xs[0], self.MARGIN_TOP, fret_xs[0], fret_bot_y))

        # Markers
        marker_y = h - (self.MARGIN_BOTTOM / 2)
        self.draw_markers(painter, fret_xs, marker_y)

        # Notes
        grid = self.instrument_model.get_note_grid()
        radius = 11
        
        for s_idx, y in enumerate(string_ys):
            for f_idx, x in enumerate(fret_xs):
                note_val = grid[s_idx, f_idx]
                
                prev_x = fret_xs[f_idx - 1] if f_idx > 0 else 0
                text_x = self.get_note_center(f_idx, x, prev_x)

                is_active = (self.scale_model.pitch_set >> note_val) & 1
                is_root = (note_val == self.scale_model.root_note)
                pen_color = QColor("white") if is_root else QColor("#929292")
                active_pen = QPen(pen_color, 2)
                
                self.draw_note_label(painter, QPointF(text_x, y), radius, note_val, is_active, is_root, 
                                     font_size=FONT_SIZE, active_pen=active_pen)

    def mousePressEvent(self, event):
        fret_xs, string_ys = self.get_geometry()
        click_pos = event.position()
        grid = self.instrument_model.get_note_grid()
        
        for s_idx, y in enumerate(string_ys):
            for f_idx, x in enumerate(fret_xs):
                prev_x = fret_xs[f_idx - 1] if f_idx > 0 else 0
                cx = self.get_note_center(f_idx, x, prev_x)
                if np.sqrt((click_pos.x()-cx)**2 + (click_pos.y()-y)**2) < 15:
                    if event.button() == Qt.LeftButton:
                        self.scale_model.toggle_note_active(grid[s_idx, f_idx])
                    elif event.button() == Qt.RightButton and f_idx == 0:
                        self.show_tuning_menu(s_idx, event.globalPosition().toPoint())
                    return

    def show_tuning_menu(self, string_idx, global_pos):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #333; color: white; }")
        for i, name in enumerate(self.scale_model.note_names):
            action = QAction(name, self)
            action.triggered.connect(lambda c, v=i: self.instrument_model.set_string_note(string_idx, v))
            menu.addAction(action)
        menu.exec(global_pos)

class FretboardView(FingerboardView):
    def get_note_center(self, f_idx, x, prev_x):
        if f_idx == 0: return x - 30
        return (prev_x + x) / 2

    def draw_markers(self, painter, fret_xs, marker_y):
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#FFFFFF"))
        def get_cx(f): return (fret_xs[f-1]+fret_xs[f])/2 if f <= self.instrument_model.num_frets else None
        
        for f in SINGLE_MARKERS:
            cx = get_cx(f)
            if cx: painter.drawEllipse(QPointF(cx, marker_y), 3, 3)
        for f in DOUBLE_MARKERS:
            cx = get_cx(f)
            if cx:
                painter.drawEllipse(QPointF(cx-6, marker_y), 3, 3)
                painter.drawEllipse(QPointF(cx+6, marker_y), 3, 3)

class FretlessView(FingerboardView):
    def get_note_center(self, f_idx, x, prev_x):
        return x

    def get_fret_line_pen(self):
        c = QColor("#AAAAAA")
        c.setAlphaF(0.2)
        return QPen(c, 1)
