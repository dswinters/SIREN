from PySide6.QtCore import QObject, Signal

class ScaleModel(QObject):
    updated = Signal()

    def __init__(self):
        super().__init__()
        self._active_notes = set(range(12))
        self._rotation_offset = 0

    @property
    def active_notes(self): return self._active_notes
    @property
    def rotation_offset(self): return self._rotation_offset

    def toggle_note_active(self, note_val):
        if note_val in self._active_notes:
            self._active_notes.remove(note_val)
        else:
            self._active_notes.add(note_val)
        self.updated.emit()

    def deactivate_all_notes(self):
        self._active_notes.clear()
        self.updated.emit()
        
    def activate_all_notes(self):
        self._active_notes = set(range(12))
        self.updated.emit()

    def rotate_view(self, direction):
        if not self._active_notes: return
        # Find next active note in direction
        for i in range(1, 13):
            candidate = (self._rotation_offset + (i * direction)) % 12
            if candidate in self._active_notes:
                self._rotation_offset = candidate
                self.updated.emit()
                break