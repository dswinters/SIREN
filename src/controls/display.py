from PySide6.QtWidgets import QComboBox
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtCore import QSize
from views.common import CYCLIC_MAPS, get_cmap

class ColormapDropdown(QComboBox):
    def __init__(self):
        super().__init__()
        self.setIconSize(QSize(100, 20))
        for name in CYCLIC_MAPS:
            self.addItem(self._create_icon(name), "", name)

    def _create_icon(self, name):
        cmap = get_cmap(name)
        w, h = 100, 20
        pixmap = QPixmap(w, h)
        painter = QPainter(pixmap)
        
        for x in range(w):
            rgba = cmap(x / (w - 1))
            c = QColor.fromRgbF(rgba[0], rgba[1], rgba[2], rgba[3] if len(rgba) > 3 else 1.0)
            painter.setPen(c)
            painter.drawLine(x, 0, x, h)
            
        painter.end()
        return QIcon(pixmap)