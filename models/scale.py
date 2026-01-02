from PySide6.QtCore import QObject, Signal

class ScaleModel(QObject):
    updated = Signal()

    def __init__(self):
        super().__init__()
        # 12-bit mask, True = active. Index 0 is the note at rotation_offset.
        self._mask = [True] * 12
        self._rotation_offset = 0

    @property
    def active_notes(self):
        # Reconstruct absolute note values for compatibility with views
        return { (self._rotation_offset + i) % 12 for i, active in enumerate(self._mask) if active }

    @property
    def mask(self):
        return list(self._mask)

    @property
    def rotation_offset(self): return self._rotation_offset

    def toggle_note_active(self, note_val):
        idx = (note_val - self._rotation_offset) % 12
        self._mask[idx] = not self._mask[idx]
        self.updated.emit()

    def set_mask(self, mask):
        if len(mask) != 12: return
        self._mask = list(mask)
        self.updated.emit()

    def deactivate_all_notes(self):
        self._mask = [False] * 12
        self.updated.emit()
        
    def activate_all_notes(self):
        self._mask = [True] * 12
        self.updated.emit()

    def rotate_modes(self, direction):
        if not any(self._mask): return
        
        # Find next active note in direction
        shift = 0
        for i in range(1, 13):
            idx = (i * direction) % 12
            if self._mask[idx]:
                shift = idx
                break
        
        # Update offset
        self._rotation_offset = (self._rotation_offset + shift) % 12
        
        # Rotate mask to preserve absolute notes (Mode Change)
        self._mask = self._mask[shift:] + self._mask[:shift]
        
        self.updated.emit()

    def transpose(self, semitones):
        # Rotate offset, keep mask same (Transposition)
        self._rotation_offset = (self._rotation_offset + semitones) % 12
        self.updated.emit()

    def set_rotation_offset(self, offset):
        target = offset % 12
        diff = (target - self._rotation_offset) % 12
        self._rotation_offset = target
        
        # Rotate mask to preserve absolute notes
        self._mask = self._mask[diff:] + self._mask[:diff]
        self.updated.emit()