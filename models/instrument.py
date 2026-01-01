import numpy as np
from PySide6.QtCore import QObject, Signal

class InstrumentModel(QObject):
    updated = Signal()

    def __init__(self, tuning=None, frets=24):
        super().__init__()
        self._num_frets = frets
        self._tuning = tuning if tuning else [4, 9, 2, 7, 11, 4]
        self._active_notes = set(range(12))
        self._rotation_offset = 0

    @property
    def num_strings(self): return len(self._tuning)
    @property
    def num_frets(self): return self._num_frets
    @property
    def tuning(self): return self._tuning
    @property
    def active_notes(self): return self._active_notes
    @property
    def rotation_offset(self): return self._rotation_offset

    def get_note_grid(self):
        tuning_vec = np.array(self._tuning)[:, np.newaxis]
        fret_vec = np.arange(self._num_frets + 1)
        return (tuning_vec + fret_vec) % 12

    def set_string_note(self, string_idx, note_val):
        if 0 <= string_idx < len(self._tuning):
            self._tuning[string_idx] = note_val
            self.updated.emit()

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

    def append_string(self):
        self._tuning.append((self._tuning[-1] + 5) % 12)
        self.updated.emit()

    def prepend_string(self):
        self._tuning.insert(0, (self._tuning[0] - 5) % 12)
        self.updated.emit()

    def remove_string(self):
        if len(self._tuning) > 1:
            self._tuning.pop()
            self.updated.emit()
