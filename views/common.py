import sys
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

try:
    from cmcrameri import cm
    CYCLIC_MAPS = sorted([name for name in cm.cmaps if name.endswith('O')])
    if "romaO" in CYCLIC_MAPS:
        CYCLIC_MAPS.insert(0, CYCLIC_MAPS.pop(CYCLIC_MAPS.index("romaO")))
except ImportError:
    print("Error: 'cmcrameri' package not found. Install via: pip install cmcrameri")
    sys.exit(1)

NOTE_NAMES = ["C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯", "A", "A♯", "B"]
FONT_SIZE = 11
INACTIVE_OPACITY = 0.15
SINGLE_MARKERS = [3, 5, 7, 9, 15, 17, 19, 21]
DOUBLE_MARKERS = [12, 24]
ACTIVE_EDGE_COLOR = "#FFFFFF"
ACTIVE_EDGE_WIDTH = 4

def get_cmap(name):
    return getattr(cm, name)

def handle_scale_key_event(event, scale_model, rotate_callback=None):
    """
    Shared key event handler for scale interactions.
    Returns True if the event was handled, False otherwise.
    """
    key = event.key()
    modifiers = event.modifiers()
    
    if rotate_callback is None:
        rotate_callback = scale_model.rotate_modes

    if key == Qt.Key_Left:
        if modifiers & Qt.ShiftModifier:
            scale_model.transpose(-1)
        else:
            rotate_callback(-1)
        return True
    elif key == Qt.Key_Right:
        if modifiers & Qt.ShiftModifier:
            scale_model.transpose(1)
        else:
            rotate_callback(1)
        return True
    elif key == Qt.Key_Up:
        scale_model.transpose(7)
        return True
    elif key == Qt.Key_Down:
        scale_model.transpose(-7)
        return True
    elif key == Qt.Key_0:
        scale_model.set_value(0)
        return True
    else:
        mapping = {
            Qt.Key_1: 0, Qt.Key_Q: 1, Qt.Key_2: 2, Qt.Key_W: 3,
            Qt.Key_3: 4, Qt.Key_4: 5, Qt.Key_R: 6, Qt.Key_5: 7,
            Qt.Key_T: 8, Qt.Key_6: 9, Qt.Key_Y: 10, Qt.Key_7: 11
        }
        if key in mapping:
            target = (scale_model.root_note + mapping[key]) % 12
            scale_model.toggle_note_active(target)
            return True
            
    return False