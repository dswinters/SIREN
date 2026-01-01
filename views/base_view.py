from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QColor
from .common import CYCLIC_MAPS, INACTIVE_OPACITY, get_cmap

class BaseNoteView(QWidget):
    def __init__(self, scale_model):
        super().__init__()
        self.scale_model = scale_model
        # Base class does NOT connect update automatically to avoid double paints in animated views
        
        self.current_cmap_name = CYCLIC_MAPS[0] if CYCLIC_MAPS else None
        self.cmap = None
        self._update_cmap()

    def set_colormap(self, name):
        self.current_cmap_name = name
        self._update_cmap()
        self.update()

    def _update_cmap(self):
        if self.current_cmap_name:
            self.cmap = get_cmap(self.current_cmap_name)

    def get_color_for_note(self, note_val, offset_override=None):
        if not self.cmap: return QColor("#333333")
        
        is_active = note_val in self.scale_model.active_notes
        if is_active:
            # Use override if provided (for smooth color transitions during animation)
            # otherwise use model state
            offset = offset_override if offset_override is not None else self.scale_model.rotation_offset
            
            relative_val = (note_val - offset) % 12
            norm_val = relative_val / 12.0
            r, g, b, a = self.cmap(norm_val) 
            return QColor.fromRgbF(r, g, b, a)
        else:
            return QColor.fromRgbF(0.6, 0.6, 0.6, INACTIVE_OPACITY)
