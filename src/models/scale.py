from PySide6.QtCore import QObject, Signal
from modules.math import rotate, intervals

class ScaleModel(QObject):
    updated = Signal()

    def __init__(self):
        super().__init__()
        # Ionian: (LSB)101011010101(MSB) = 2741
        self._shape = 2741
        self._root_note = 0

    @property
    def number(self):
        # Return bit-rotated binary literal
        n = self._root_note
        return rotate(self._shape, -n)

    @property
    def shape(self):
        return self._shape

    @property
    def root_note(self): return self._root_note

    def is_diatonic(self):
        mask = 2741
        for i in range(12):
            rotated = rotate(mask, i)
            if self._shape == rotated:
                return True
        return False

    def toggle_note_active(self, note_val):
        idx = (note_val - self._root_note) % 12
        self._shape ^= (1 << idx)
        self.updated.emit()

    def set_shape(self, shape):
        self._shape = shape & 0xFFF
        self.updated.emit()

    def rotate_modes(self, direction):
        if self._shape == 0: return
        
        # Find next active bit in direction
        if direction == 1:
            shift = intervals(self._shape, 0)
        else:
            shift = -intervals(self._shape, 0, direction='descending')
        
        # Update offset
        self._root_note = (self._root_note + shift) % 12
        
        # Rotate shape right by shift to preserve absolute notes (Mode Change)
        # Right rotate: (val >> s) | (val << (12-s))
        s = shift
        self._shape = rotate(self._shape, s)
        
        self.updated.emit()

    def transpose(self, semitones):
        # Rotate offset, keep shape same (Transposition)
        self._root_note = (self._root_note + semitones) % 12
        self.updated.emit()

    def transpose_mask(self, semitones):
        mask = self.number
        return rotate(mask, semitones)

    def set_root_note(self, offset):
        target = offset % 12
        diff = (target - self._root_note) % 12
        self._root_note = target
        
        # Rotate shape right by diff to preserve absolute notes
        s = diff
        self._shape = rotate(self._shape, s)
        self.updated.emit()