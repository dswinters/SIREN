import math
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QFont, QColor, QPen, QPolygonF, QLinearGradient, QBrush
from PySide6.QtCore import Qt, QPointF, QRectF
from .base_view import BaseNoteView
from .mixins import PlaybackHighlightMixin
from .common import INACTIVE_OPACITY, ACTIVE_EDGE_COLOR, ACTIVE_EDGE_WIDTH

class TonnetzView(BaseNoteView, PlaybackHighlightMixin):
    def __init__(self, scale_model):
        super().__init__(scale_model)
        self.scale_model.updated.connect(self.update)
        self.setWindowTitle("Tonnetz Grid")
        self.resize(800, 600)
        self.setStyleSheet("background-color: #121212;")
        self.init_highlight_animation()

        self.node_radius = 20
        self.spacing = 70

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()

        # Fixed 7x7 Grid (Core)
        core_cols = 7
        core_rows = 7

        # Calculate bounds in unit space (spacing = 1)
        # x = c - 0.5 * r
        # y = r * sqrt(3) / 2

        # X range: [-4.5, 7.5] -> Width = 12
        # Y range: [-0.5*sqrt(3), 3.5*sqrt(3)] -> Height = 4*sqrt(3)

        unit_w = 12.0
        unit_h = 4.0 * math.sqrt(3)

        # Padding
        padding = 40
        avail_w = w - 2 * padding
        avail_h = h - 2 * padding

        if avail_w <= 0 or avail_h <= 0:
            return

        scale_x = avail_w / unit_w
        scale_y = avail_h / unit_h

        self.spacing = min(scale_x, scale_y)
        self.node_radius = min(20, self.spacing * 0.35)

        cx = w / 2
        cy = h / 2

        # Center of the grid in unit space
        unit_cx = 1.5
        unit_cy = 1.5 * math.sqrt(3)

        def to_screen(c, r):
            ux = c - 0.5 * r
            uy = r * math.sqrt(3) / 2
            x = cx + (ux - unit_cx) * self.spacing
            y = cy - (uy - unit_cy) * self.spacing
            return x, y

        grid_points = {}
        for r in range(-1, core_rows + 1):
            for c in range(-1, core_cols + 1):
                x, y = to_screen(c, r)
                # Value calculation: +7 per column (c), +9 per row (r)
                val = (self.scale_model.root_note + c * 7 + r * 9 + 6) % 12

                grid_points[(c, r)] = (x, y, val)

        def draw_triads(mask, offsets, color_idx):
            if not (mask and self.cmap): return

            r, g, b, a = self.cmap(color_idx / 12.0)
            base_color = QColor.fromRgbF(r, g, b, a)
            triad_color = QColor(base_color)
            triad_color.setAlphaF(triad_color.alphaF() * 0.6)

            painter.setPen(Qt.NoPen)
            painter.setBrush(triad_color)

            for (c, r), (x, y, val) in grid_points.items():
                if not ((mask >> val) & 1):
                    continue

                points = []
                valid = True
                for dc, dr in offsets:
                    nk = (c + dc, r + dr)
                    if nk not in grid_points:
                        valid = False
                        break
                    nx, ny, _ = grid_points[nk]
                    points.append(QPointF(nx, ny))

                if valid:
                    painter.drawPolygon(QPolygonF(points))

        mask = self.scale_model.pitch_set

        # Major Triads (Color 5): Node (Root), Up-Right (M3, +4), Right (5th, +7)
        major_mask = mask & self.scale_model.transpose_mask(4) & self.scale_model.transpose_mask(7)
        draw_triads(major_mask, [(0,0), (1,1), (0,1)], 5)

        # Minor Triads (Color 10): Node (m3), Up (Root, -3), Up-Right (5th, +4)
        minor_mask = mask & self.scale_model.transpose_mask(-3) & self.scale_model.transpose_mask(4)
        # Neighbors: (0,0), (1,0), (1,1)
        draw_triads(minor_mask, [(0,0), (1,0), (1,1)], 10)

        # Draw Edges
        # We draw "forward" edges to avoid duplicates and cover the requested neighbors:
        # (-1,0), (1,0), (0,1), (1,1), (-1,1), (0,-1)
        # Forward edges to draw from (c,r): (1,0), (0,1), (1,1), (-1,1)
        default_pen = QPen(QColor("#333333"), 2)
        active_pen = QPen(QColor(ACTIVE_EDGE_COLOR), ACTIVE_EDGE_WIDTH)

        for (c, r), (x, y, val) in grid_points.items():
            neighbors = [
                (c + 1, r),     # (1, 0)
                (c, r + 1),     # (0, 1)
                (c + 1, r + 1), # (1, 1)
            ]

            is_active_source = (self.scale_model.pitch_set >> val) & 1

            for nc, nr in neighbors:
                if (nc, nr) in grid_points:
                    nx, ny, nval = grid_points[(nc, nr)]
                    is_active_target = (self.scale_model.pitch_set >> nval) & 1

                    pen = QPen(active_pen if (is_active_source and is_active_target) else default_pen)

                    painter.setPen(pen)

                    # Calculate vector for clipping
                    dx = nx - x
                    dy = ny - y
                    dist = math.hypot(dx, dy)

                    if dist > 0:
                        ux = dx / dist
                        uy = dy / dist

                        # Clip lines to edge of label radius
                        p1 = QPointF(x + ux * self.node_radius, y + uy * self.node_radius)
                        p2 = QPointF(nx - ux * self.node_radius, ny - uy * self.node_radius)
                        painter.drawLine(p1, p2)

        # Draw Nodes
        font_size = max(8, int(self.node_radius * 0.8))
        painter.setFont(QFont("Arial", font_size, QFont.Bold))

        for (c, r), (x, y, val) in grid_points.items():
            is_active = (self.scale_model.pitch_set >> val) & 1
            is_root = (val == self.scale_model.root_note)

            active_pen = None
            if is_active:
                base_pen = QColor("white")
                pen_color = self.get_interpolated_color(val, base_pen, QColor("#409C40"))
                active_pen = QPen(pen_color, 3)

            self.draw_note_label(painter, QPointF(x, y), self.node_radius, val, is_active, is_root,
                                 font_size=font_size, opacity=1.0, active_pen=active_pen)

        self._grid_points = grid_points

        bg_r, bg_g, bg_b = 18, 18, 18
        bg_color = QColor(bg_r, bg_g, bg_b, 255)
        bg_transparent = QColor(bg_r, bg_g, bg_b, 0)
        
        def draw_fade(p1, p2):
            # 1) Direction p2 -> p1
            diff = p1 - p2
            length = math.hypot(diff.x(), diff.y())
            if length == 0: return
            uw = diff / length
            uh = QPointF(uw.y(), -uw.x())
            m = (p1 + p2) / 2
            rect_w = max(w, h)
            rect_h = 2*self.spacing
            
            v1 = m + uw * (rect_w / 2)
            v2 = m - uw * (rect_w / 2)
            v3 = v2 + uh * rect_h
            v4 = v1 + uh * rect_h
            
            poly = QPolygonF([v1, v2, v3, v4])
            
            grad = QLinearGradient(m, m + uh * rect_h)
            grad.setColorAt(0, bg_transparent)
            grad.setColorAt(0.4, bg_color)
            
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.NoPen)
            painter.drawPolygon(poly)


        pt = lambda c, r: QPointF(*to_screen(c, r))
        
        p_ll = pt(0, 0)
        p_lr = pt(core_cols - 1, 0)
        p_ur = pt(core_cols - 1, core_rows - 1)
        p_ul = pt(0, core_rows - 1)

        edges = [
            (p_ll, p_lr),
            (p_lr, p_ur),
            (p_ur, p_ul),
            (p_ul, p_ll)
        ]

        for p1, p2 in edges:
            draw_fade(p1, p2)

    def mousePressEvent(self, event):
        if not hasattr(self, '_grid_points'): return

        pos = event.position()

        for (c, r), (x, y, val) in self._grid_points.items():
            if math.hypot(pos.x() - x, pos.y() - y) < self.node_radius:
                if event.button() == Qt.LeftButton:
                    self.scale_model.toggle_note_active(val)
                elif event.button() == Qt.RightButton:
                    self.scale_model.set_root_note(val)
                return