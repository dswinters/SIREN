from PySide6.QtCore import QObject, Signal

class ScaleModel(QObject):
    updated = Signal()

    def __init__(self):
        super().__init__()
        # Ionian: 101011010101 -> 2741
        self._value = 2741
        self._root_note = 0
        self._force_accidental = None # None (Auto), 'sharp', 'flat'

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
        return ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    def _get_flat_names(self):
        return ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

    def _solve_naming(self, active_set, use_sharps):
        # Columns: C, D, E, F, G, A, B
        # Each column has 2 options: Natural and (Sharp if use_sharps else Flat)
        
        # Options structure: list of (value, name, is_accidental)
        # Natural row: C(0), D(2), E(4), F(5), G(7), A(9), B(11)
        naturals = [
            (0, "C"), (2, "D"), (4, "E"), (5, "F"), (7, "G"), (9, "A"), (11, "B")
        ]
        
        # Accidental row
        if use_sharps:
            # Sharp row: C#(1), D#(3), E#(5), F#(6), G#(8), A#(10), B#(0)
            accidentals = [
                (1, "C#"), (3, "D#"), (5, "E#"), (6, "F#"), (8, "G#"), (10, "A#"), (0, "B#")
            ]
        else:
            # Flat row: Cb(11), Db(1), Eb(3), Fb(4), Gb(6), Ab(8), Bb(10)
            accidentals = [
                (11, "Cb"), (1, "Db"), (3, "Eb"), (4, "Fb"), (6, "Gb"), (8, "Ab"), (10, "Bb")
            ]
            
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

    def _is_using_sharps(self):
        # 1. Check Force
        if self._force_accidental == 'sharp': return True
        if self._force_accidental == 'flat': return False

        # 2. Diatonic Logic
        active_set = set()
        mask = self.active_notes
        for i in range(12):
            if (mask >> i) & 1:
                active_set.add(i)

        sharp_sol = self._solve_naming(active_set, True)
        flat_sol = self._solve_naming(active_set, False)
        
        if sharp_sol or flat_sol:
            if sharp_sol and not flat_sol: return True
            if flat_sol and not sharp_sol: return False
            # Both exist
            s_acc = sum(1 for _, _, is_acc in sharp_sol if is_acc)
            f_acc = sum(1 for _, _, is_acc in flat_sol if is_acc)
            
            if f_acc < s_acc: return False
            elif s_acc < f_acc: return True
            else:
                return self._root_note not in [1, 3, 5, 8, 10]

        # 3. Non-Diatonic Logic
        s_names = self._get_sharp_names()
        f_names = self._get_flat_names()
        s_count = 0
        f_count = 0
        for i in range(12):
            if (mask >> i) & 1:
                if '#' in s_names[i]: s_count += 1
                if 'b' in f_names[i]: f_count += 1
        
        if f_count < s_count: return False
        elif s_count < f_count: return True
        else:
            return self._root_note not in [1, 3, 5, 8, 10]

    @property
    def note_names(self):
        # Get active notes as a set of integers
        active_set = set()
        mask = self.active_notes
        for i in range(12):
            if (mask >> i) & 1:
                active_set.add(i)

        # Try to solve for both representations
        sharp_sol = self._solve_naming(active_set, True)
        flat_sol = self._solve_naming(active_set, False)
        
        # Determine winner
        winner = None
        
        if self._force_accidental == 'sharp' and sharp_sol:
            winner = (sharp_sol, True)
        elif self._force_accidental == 'flat' and flat_sol:
            winner = (flat_sol, False)
        elif sharp_sol and not flat_sol:
            winner = (sharp_sol, True)
        elif flat_sol and not sharp_sol:
            winner = (flat_sol, False)
        elif sharp_sol and flat_sol:
            # Tie-breaker: fewest accidentals
            s_acc = sum(1 for _, _, is_acc in sharp_sol if is_acc)
            f_acc = sum(1 for _, _, is_acc in flat_sol if is_acc)
            
            if f_acc < s_acc:
                winner = (flat_sol, False)
            elif s_acc < f_acc:
                winner = (sharp_sol, True)
            else:
                # Tie-breaker based on root preference
                if self._root_note in [1, 3, 5, 8, 10]:
                    winner = (flat_sol, False)
                else:
                    winner = (sharp_sol, True)

        if winner:
            sol, is_sharp_rep = winner
            # Build full name list
            names = self._get_sharp_names() if is_sharp_rep else self._get_flat_names()
            for val, name, _ in sol:
                names[val] = name
            return names

        # 2. Non-Diatonic / Fallback Logic
        s_names = self._get_sharp_names()
        f_names = self._get_flat_names()

        if self._force_accidental == 'sharp':
            return s_names
        if self._force_accidental == 'flat':
            return f_names

        # Auto-detect: Count accidentals in active notes
        s_count = 0
        f_count = 0
        for i in range(12):
            if (mask >> i) & 1:
                if '#' in s_names[i]: s_count += 1
                if 'b' in f_names[i]: f_count += 1
        
        if f_count < s_count:
            return f_names
        elif s_count < f_count:
            return s_names
        else:
            if self._root_note in [1, 3, 5, 8, 10]:
                return f_names
            return s_names

    def toggle_naming_convention(self):
        currently_sharps = self._is_using_sharps()
        target_is_sharps = not currently_sharps

        active_set = set()
        mask = self.active_notes
        for i in range(12):
            if (mask >> i) & 1:
                active_set.add(i)

        current_valid = self._solve_naming(active_set, currently_sharps) is not None
        target_valid = self._solve_naming(active_set, target_is_sharps) is not None

        if current_valid and not target_valid:
            return

        if currently_sharps:
            self._force_accidental = 'flat'
        else:
            self._force_accidental = 'sharp'
        self.updated.emit()

    def toggle_note_active(self, note_val):
        idx = (note_val - self._root_note) % 12
        self._value ^= (1 << idx)
        self.updated.emit()

    def set_value(self, val):
        self._value = val & 0xFFF
        self._force_accidental = None
        self.updated.emit()

    def deactivate_all_notes(self):
        self._value = 0
        self._force_accidental = None
        self.updated.emit()
        
    def activate_all_notes(self):
        self._value = 0xFFF
        self._force_accidental = None
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
        
        self._force_accidental = None
        self.updated.emit()

    def transpose(self, semitones):
        # Rotate offset, keep value same (Transposition)
        self._root_note = (self._root_note + semitones) % 12
        self._force_accidental = None
        self.updated.emit()

    def set_root_note(self, offset):
        target = offset % 12
        diff = (target - self._root_note) % 12
        self._root_note = target
        
        # Rotate value right by diff to preserve absolute notes
        s = diff
        self._value = ((self._value >> s) | (self._value << (12 - s))) & 0xFFF
        self._force_accidental = None
        self.updated.emit()