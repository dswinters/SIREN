from PySide6.QtCore import QObject, Signal

class ScaleModel(QObject):
    updated = Signal()

    SHARP_NAMES = ["C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯", "A", "A♯", "B"]
    FLAT_NAMES = ["C", "D♭", "D", "E♭", "E", "F", "G♭", "G", "A♭", "A", "B♭", "B"]

    _NATURALS = [
        (0, "C"), (2, "D"), (4, "E"), (5, "F"), (7, "G"), (9, "A"), (11, "B")
    ]
    _SHARP_ACCIDENTALS = [
        (1, "C♯"), (3, "D♯"), (5, "E♯"), (6, "F♯"), (8, "G♯"), (10, "A♯"), (0, "B♯")
    ]
    _FLAT_ACCIDENTALS = [
        (11, "C♭"), (1, "D♭"), (3, "E♭"), (4, "F♭"), (6, "G♭"), (8, "A♭"), (10, "B♭")
    ]

    def __init__(self):
        super().__init__()
        # Ionian: (LSB)101011010101(MSB) = 2741
        self._value = 2741
        self._root_note = 0
        self._accidental_mode = 'sharp'
        self._sharp_rep = None
        self._flat_rep = None
        self._update_representations()

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

    def is_diatonic(self):
        mask = 2741
        for i in range(12):
            rotated = ((mask >> i) | (mask << (12 - i))) & 0xFFF
            if self._value == rotated:
                return True
        return False

    def _get_sharp_names(self):
        return list(self.SHARP_NAMES)

    def _get_flat_names(self):
        return list(self.FLAT_NAMES)

    def _solve_naming(self, active_set, use_sharps):
        # Columns: C, D, E, F, G, A, B
        # Each column has 2 options: Natural and (Sharp if use_sharps else Flat)

        naturals = self._NATURALS
        accidentals = self._SHARP_ACCIDENTALS if use_sharps else self._FLAT_ACCIDENTALS
            
        # Recursive solver
        # Returns list of (value, name, is_accidental) or None
        def solve(col_idx, notes_to_cover):
            if col_idx == 7:
                return [] if not notes_to_cover else None
            
            # Candidates for this column
            col_opts = []
            
            # Option 1: Natural
            val_n, name_n = naturals[col_idx]
            if val_n in notes_to_cover:
                col_opts.append((val_n, name_n, False))
                
            # Option 2: Accidental
            val_a, name_a = accidentals[col_idx]
            if val_a in notes_to_cover:
                col_opts.append((val_a, name_a, True))
                
            for val, name, is_acc in col_opts:
                # Recurse
                res = solve(col_idx + 1, notes_to_cover - {val})
                if res is not None:
                    return [(val, name, is_acc)] + res
            
            return None

        return solve(0, active_set)

    def _is_harmonic(self):
        # C Harmonic Minor: 101101011001, bit-reversed = 2477
        mask = 2477
        for i in range(12):
            rotated = ((mask >> i) | (mask << (12 - i))) & 0xFFF
            if self._value == rotated:
                return True, i
        return False, 0

    def _compute_representation(self, use_sharps):
        # Get active notes (absolute)
        active_set = set()
        mask = self.active_notes
        for i in range(12):
            if (mask >> i) & 1:
                active_set.add(i)

        # 1. Harmonic Minor Logic
        is_harm, offset = self._is_harmonic()
        if is_harm:
            # Target relative to pattern root (index 0 of _value)
            rel_target = (11 - offset) % 12
            # Target absolute
            abs_target = (rel_target + self._root_note) % 12
            # Diatonic proxy (semitone down)
            abs_proxy = (abs_target - 1) % 12
            
            if abs_target in active_set:
                proxy_set = active_set.copy()
                proxy_set.remove(abs_target)
                proxy_set.add(abs_proxy)
                
                sol = self._solve_naming(proxy_set, use_sharps)
                if sol:
                    # Build names list
                    names = self._get_sharp_names() if use_sharps else self._get_flat_names()
                    for val, name, _ in sol:
                        names[val] = name
                    
                    # Fix target label
                    base_name = names[abs_proxy]
                    if base_name.endswith('♭'):
                        new_name = base_name[:-1] + "♮"
                    elif base_name.endswith('♯'):
                        new_name = base_name[:-1] + "𝄪"
                    else:
                        new_name = base_name + "♯"
                    names[abs_target] = new_name
                    return names

        # 2. Standard Logic
        sol = self._solve_naming(active_set, use_sharps)
        if sol:
            names = self._get_sharp_names() if use_sharps else self._get_flat_names()
            for val, name, _ in sol:
                names[val] = name
            return names
            
        return None

    def _update_representations(self):
        self._sharp_rep = self._compute_representation(True)
        self._flat_rep = self._compute_representation(False)
        
        # Determine mode
        if self._sharp_rep and self._flat_rep:
            # Count accidentals
            def count_acc(names):
                c = 0
                for n in names:
                    if '♯' in n: c += 1
                    if '♭' in n: c += 1
                    if '𝄪' in n: c += 2
                return c

            s_count = count_acc(self._sharp_rep)
            f_count = count_acc(self._flat_rep)
            
            if f_count < s_count:
                self._accidental_mode = 'flat'
            elif s_count < f_count:
                self._accidental_mode = 'sharp'
            else:
                # Tie-breaker
                if self._root_note in [1, 3, 5, 8, 10]:
                    self._accidental_mode = 'flat'
                else:
                    self._accidental_mode = 'sharp'
                    
        elif self._sharp_rep:
            self._accidental_mode = 'sharp'
        elif self._flat_rep:
            self._accidental_mode = 'flat'
        else:
            # Both invalid (e.g. Chromatic)
            # Fallback to simple count
            s_names = self._get_sharp_names()
            f_names = self._get_flat_names()
            mask = self.active_notes
            s_count = 0
            f_count = 0
            for i in range(12):
                if (mask >> i) & 1:
                    if '♯' in s_names[i]: s_count += 1
                    if '♭' in f_names[i]: f_count += 1
            
            if f_count < s_count:
                self._accidental_mode = 'flat'
            elif s_count < f_count:
                self._accidental_mode = 'sharp'
            else:
                if self._root_note in [1, 3, 5, 8, 10]:
                    self._accidental_mode = 'flat'
                else:
                    self._accidental_mode = 'sharp'

    @property
    def note_names(self):
        if self._accidental_mode == 'sharp':
            if self._sharp_rep: return self._sharp_rep
            return self._get_sharp_names()
        else:
            if self._flat_rep: return self._flat_rep
            return self._get_flat_names()

    def toggle_naming_convention(self):
        if self._accidental_mode == 'sharp':
            # Try switching to flat
            if self._flat_rep is not None:
                self._accidental_mode = 'flat'
                self.updated.emit()
            elif self._sharp_rep is None:
                # Both invalid, allow toggle
                self._accidental_mode = 'flat'
                self.updated.emit()
        else:
            # Try switching to sharp
            if self._sharp_rep is not None:
                self._accidental_mode = 'sharp'
                self.updated.emit()
            elif self._flat_rep is None:
                # Both invalid, allow toggle
                self._accidental_mode = 'sharp'
                self.updated.emit()

    def toggle_note_active(self, note_val):
        idx = (note_val - self._root_note) % 12
        self._value ^= (1 << idx)
        self._update_representations()
        self.updated.emit()

    def set_value(self, val):
        self._value = val & 0xFFF
        self._update_representations()
        self.updated.emit()

    def deactivate_all_notes(self):
        self._value = 0
        self._update_representations()
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
        
        self._update_representations()
        self.updated.emit()

    def transpose(self, semitones):
        # Rotate offset, keep value same (Transposition)
        self._root_note = (self._root_note + semitones) % 12
        self._update_representations()
        self.updated.emit()

    def transpose_mask(self, semitones):
        mask = self.active_notes
        return ((mask >> (semitones % 12)) | (mask << (12 - (semitones % 12)))) & 0xFFF


    def set_root_note(self, offset):
        target = offset % 12
        diff = (target - self._root_note) % 12
        self._root_note = target
        
        # Rotate value right by diff to preserve absolute notes
        s = diff
        self._value = ((self._value >> s) | (self._value << (12 - s))) & 0xFFF
        self._update_representations()
        self.updated.emit()