import numpy as np
from PySide6.QtCore import QObject, Signal

class InstrumentModel(QObject):
    updated = Signal()

    def __init__(self, tuning=None, frets=24):
        super().__init__()
        self._num_frets = frets
        self._tuning = tuning if tuning else [4, 9, 2, 7, 11, 4]

    @property
    def num_strings(self): return len(self._tuning)
    @property
    def num_frets(self): return self._num_frets
    @property
    def tuning(self): return self._tuning

    def get_note_grid(self):
        tuning_vec = np.array(self._tuning)[:, np.newaxis]
        fret_vec = np.arange(self._num_frets + 1)
        return (tuning_vec + fret_vec) % 12

    def set_string_note(self, string_idx, note_val):
        if 0 <= string_idx < len(self._tuning):
            self._tuning[string_idx] = note_val
            self.updated.emit()

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
