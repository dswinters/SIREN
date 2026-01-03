from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPen, QColor, QFont
from PySide6.QtCore import Qt, QRectF

class KeySignatureView(QWidget):
    def __init__(self, scale_model):
        super().__init__()
        self.scale_model = scale_model
        self.scale_model.updated.connect(self.update)
        self.setFixedWidth(160)
        self.setFixedHeight(90)
        self.setStyleSheet("background-color: #121212;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # Draw Staff Lines
        line_spacing = 9
        # 5 lines, 4 spaces. Height = 4 * 9 = 36.
        start_y = (h - 36) / 2
        
        painter.setPen(QPen(QColor("#555555"), 1))
        for i in range(5):
            y = start_y + i * line_spacing
            painter.drawLine(0, y, w, y)
            
        # Draw Clef
        painter.setPen(QColor("#999999"))
        painter.setFont(QFont("Times New Roman", 36))
        painter.drawText(0, 0, 40, h, Qt.AlignCenter, "𝄞")
        
        # Collect accidentals from active notes
        accs = []
        mask = self.scale_model.active_notes
        names = self.scale_model.note_names
        
        for i in range(12):
            if (mask >> i) & 1:
                n = names[i]
                if len(n) > 1:
                    letter = n[0]
                    symbol = n[1]
                    if symbol in ['♯', '♭', '𝄪', '♮']:
                        accs.append((letter, symbol))

        # Sort based on accidental mode
        mode = self.scale_model._accidental_mode
        if mode == 'flat':
            # Circle of Fifths order for flats: B E A D G C F
            order = "BEADGCF"
            accs.sort(key=lambda x: order.index(x[0]) if x[0] in order else 99)
        else:
            # Circle of Fifths order for sharps: F C G D A E B
            order = "FCGDAEB"
            accs.sort(key=lambda x: order.index(x[0]) if x[0] in order else 99)

        # Draw Accidentals
        painter.setPen(QColor("#CCCCCC"))
        painter.setFont(QFont("Arial", 22))
        
        # Y-offsets from top line (F5) in half-steps (4.5px)
        # Positive is down
        sharp_map = {'F': 0, 'C': 3, 'G': -1, 'D': 2, 'A': 5, 'E': 1, 'B': 4}
        flat_map  = {'B': 4, 'E': 1, 'A': 5, 'D': 2, 'G': 6, 'C': 3, 'F': 7}
        
        start_x = 50
        spacing_x = 15
        
        for i, (letter, symbol) in enumerate(accs):
            # Determine Y position
            if symbol == '♭':
                y_off = flat_map.get(letter, 0)
            elif symbol == '♯':
                y_off = sharp_map.get(letter, 0)
            else:
                # Fallback for natural/double-sharp: use sharp map usually
                y_off = sharp_map.get(letter, 0)
                
            y = start_y + (y_off * 4.5)
            x = start_x + (i * spacing_x)
            
            rect = QRectF(x, y - 15, 20, 30)
            painter.drawText(rect, Qt.AlignCenter, symbol)