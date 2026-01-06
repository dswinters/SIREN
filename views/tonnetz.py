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
                # Value calculation: +7 per column (c), +8 per row (r)
                val = (self.scale_model.root_note + c * 7 + r * 8 + 6) % 12

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

        mask = self.scale_model.active_notes

        # Major Triads (Color 6): Node (3rd), Up (Root, -4), Up-Right (5th, +3)
        major_mask = mask & self.scale_model.transpose_mask(-4) & self.scale_model.transpose_mask(3)
        # Neighbors: (0,0), (0,1), (1,1)
        draw_triads(major_mask, [(0,0), (0,1), (1,1)], 5)

        # Minor Triads (Color 10): Node (Root), Right (5th, +7), Up-Right (3rd, +3)
        minor_mask = mask & self.scale_model.transpose_mask(3) & self.scale_model.transpose_mask(7)
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

            is_active_source = (self.scale_model.active_notes >> val) & 1

            for nc, nr in neighbors:
                if (nc, nr) in grid_points:
                    nx, ny, nval = grid_points[(nc, nr)]
                    is_active_target = (self.scale_model.active_notes >> nval) & 1

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
            is_active = (self.scale_model.active_notes >> val) & 1
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
        
        # Extension to ensure overlap with grid lines
        ext = 5

        # Draw Fade Overlay (Bottom)
        # r=0 is bottom main row, r=-1 is bottom pad row
        _, y_main_bottom = to_screen(0, 0)
        _, y_pad_bottom = to_screen(0, -1)

        # Extend rect slightly past y_pad_bottom
        rect_bottom = QRectF(0, y_main_bottom, w, (y_pad_bottom - y_main_bottom) + ext)

        grad_bottom = QLinearGradient(0, y_main_bottom, 0, y_pad_bottom)
        grad_bottom.setColorAt(0, bg_transparent)
        grad_bottom.setColorAt(0.95, bg_color) # Sharper ramp
        grad_bottom.setColorAt(1, bg_color)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(grad_bottom))
        painter.drawRect(rect_bottom)

        # Solid black below
        rect_solid_bottom = QRectF(0, y_pad_bottom, w, h - y_pad_bottom)
        painter.setBrush(bg_color)
        painter.drawRect(rect_solid_bottom)

        # Draw Fade Overlay (Top)
        # r=core_rows-1 is top main row, r=core_rows is top pad row
        _, y_main_top = to_screen(0, core_rows - 1)
        _, y_pad_top = to_screen(0, core_rows)

        # Extend rect slightly above y_pad_top
        rect_top = QRectF(0, y_pad_top - ext, w, (y_main_top - y_pad_top) + ext)
        
        grad_top = QLinearGradient(0, y_main_top, 0, y_pad_top)
        grad_top.setColorAt(0, bg_transparent)
        grad_top.setColorAt(0.95, bg_color)
        grad_top.setColorAt(1, bg_color)
        
        painter.setBrush(QBrush(grad_top))
        painter.drawRect(rect_top)

        # Solid background above
        rect_solid_top = QRectF(0, 0, w, y_pad_top)
        painter.setBrush(bg_color)
        painter.drawRect(rect_solid_top)

        # Draw Fade Overlay (Left & Right) - Slanted
        # We use polygons to match the grid slant
        mid_r = (core_rows - 1) / 2.0
        
        for col_idx, is_left in [(0, True), (core_cols, False)]:
            # Inner line is at col_idx if right, col_idx-1 if left? 
            # Left fade: c=0 (inner) to c=-1 (outer)
            # Right fade: c=core_cols-1 (inner) to c=core_cols (outer)
            
            c_inner = -1 if is_left else core_cols - 1
            c_outer = -2 if is_left else core_cols # Extend further out
            
            # Actually, let's just use the pad columns:
            # Left: c=0 to c=-1. Right: c=core_cols-1 to c=core_cols.
            c_in = 0 if is_left else core_cols - 1
            c_out = -1 if is_left else core_cols
            
            p_in_top = QPointF(*to_screen(c_in, core_rows))
            p_in_bot = QPointF(*to_screen(c_in, -1))
            p_out_top = QPointF(*to_screen(c_out, core_rows))
            p_out_bot = QPointF(*to_screen(c_out, -1))
            
            # Extend the outer points slightly to ensure overlap
            # Vector from in to out
            v_ext_top = p_out_top - p_in_top
            v_ext_bot = p_out_bot - p_in_bot
            # Scale slightly > 1.0 or just add a fixed amount? 
            # Let's just use the gradient extrapolation (PadSpread) and extend geometry
            p_ext_top = p_out_top + (v_ext_top * 0.2)
            p_ext_bot = p_out_bot + (v_ext_bot * 0.2)
            
            # Extend the outer points slightly to ensure overlap
            # Vector from in to out
            v_ext_top = p_out_top - p_in_top
            v_ext_bot = p_out_bot - p_in_bot
            # Scale slightly > 1.0 or just add a fixed amount? 
            # Let's just use the gradient extrapolation (PadSpread) and extend geometry
            p_ext_top = p_out_top + (v_ext_top * 0.2)
            p_ext_bot = p_out_bot + (v_ext_bot * 0.2)
            
            poly = QPolygonF([p_in_top, p_in_bot, p_ext_bot, p_ext_top])
            
            # Calculate Gradient Vector perpendicular to the edge
            p_edge_1 = QPointF(*to_screen(c_in, 0))
            p_edge_2 = QPointF(*to_screen(c_in, 1))
            v_edge = p_edge_2 - p_edge_1
            
            v_perp = QPointF(-v_edge.y(), v_edge.x())
            
            p_start = QPointF(*to_screen(c_in, mid_r))
            p_outer = QPointF(*to_screen(c_out, mid_r))
            v_diff = p_outer - p_start
            
            dot_prod = v_diff.x() * v_perp.x() + v_diff.y() * v_perp.y()
            len_sq = v_perp.x()**2 + v_perp.y()**2
            
            if len_sq > 0:
                t = dot_prod / len_sq
                v_grad = QPointF(v_perp.x() * t, v_perp.y() * t)
                p_end = p_start + v_grad
            else:
                p_end = p_outer

            grad = QLinearGradient(p_start, p_end)
            grad.setColorAt(0, bg_transparent)
            grad.setColorAt(0.95, bg_color)
            grad.setColorAt(1, bg_color)
            
            painter.setBrush(QBrush(grad))
            painter.drawPolygon(poly)
            
            # Solid block beyond the fade
            # Extend 2000px outwards
            shift = -2000 if is_left else 2000
            p_far_top = QPointF(p_out_top.x() + shift, p_out_top.y())
            p_far_bot = QPointF(p_out_bot.x() + shift, p_out_bot.y())
            
            poly_solid = QPolygonF([p_out_top, p_out_bot, p_far_bot, p_far_top])
            painter.setBrush(bg_color)
            painter.drawPolygon(poly_solid)

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