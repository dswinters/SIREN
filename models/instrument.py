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

    def set_tuning(self, tuning):
        self._tuning = list(tuning)
        self.updated.emit()
