import sys
from PySide6.QtGui import QColor

try:
    from cmcrameri import cm
    CYCLIC_MAPS = sorted([name for name in cm.cmaps if name.endswith('O')])
except ImportError:
    print("Error: 'cmcrameri' package not found. Install via: pip install cmcrameri")
    sys.exit(1)

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
FONT_SIZE = 11
INACTIVE_OPACITY = 0.15
SINGLE_MARKERS = [3, 5, 7, 9, 15, 17, 19, 21]
DOUBLE_MARKERS = [12, 24]

def get_cmap(name):
    return getattr(cm, name)