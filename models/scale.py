from PySide6.QtCore import QObject, Signal

class ScaleModel(QObject):
    updated = Signal()

    def __init__(self):
        super().__init__()
        # Ionian: 101011010101 -> 2741
        self._value = 2741
        self._root_note = 0

    @property
    def active_notes(self):
        # Return bit-rotated binary literal
        n = self._root_note
        return ((self._value << n) | (self._value >> (12 - n))) & 0xFFF

    @property
    def value(self):
        return self._value

    @property
    def root_note(self): return self._root_note

    def toggle_note_active(self, note_val):
        idx = (note_val - self._root_note) % 12
        self._value ^= (1 << idx)
        self.updated.emit()

    def set_value(self, val):
        self._value = val & 0xFFF
        self.updated.emit()

    def deactivate_all_notes(self):
        self._value = 0
        self.updated.emit()
        
    def activate_all_notes(self):
        self._value = 0xFFF
        self.updated.emit()

    def rotate_modes(self, direction):
        if self._value == 0: return
        
        # Find next active bit in direction
        shift = 0
        for i in range(1, 13):
            idx = (i * direction) % 12
            if (self._value >> idx) & 1:
                shift = idx
                break
        
        # Update offset
        self._root_note = (self._root_note + shift) % 12
        
        # Rotate value right by shift to preserve absolute notes (Mode Change)
        # Right rotate: (val >> s) | (val << (12-s))
        s = shift
        self._value = ((self._value >> s) | (self._value << (12 - s))) & 0xFFF
        
        self.updated.emit()

    def transpose(self, semitones):
        # Rotate offset, keep value same (Transposition)
        self._root_note = (self._root_note + semitones) % 12
        self.updated.emit()

    def set_root_note(self, offset):
        target = offset % 12
        diff = (target - self._root_note) % 12
        self._root_note = target
        
        # Rotate value right by diff to preserve absolute notes
        s = diff
        self._value = ((self._value >> s) | (self._value << (12 - s))) & 0xFFF
        self.updated.emit()