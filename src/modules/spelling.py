from PySide6.QtCore import QObject, Signal
from .math import rotate

class Spelling(QObject):
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

    def __init__(self, scale_model):
        super().__init__()
        self._scale_model = scale_model
        self._scale_model.updated.connect(self._update_spellings)
        
        self._enharmonic_mode = 'sharp'
        self._sharp_spelling = None
        self._flat_spelling = None
        self._note_names = list(self.SHARP_NAMES)
        
        self._update_spellings()

    @property
    def note_names(self):
        return self._note_names

    @property
    def enharmonic_mode(self):
        return self._enharmonic_mode

    def toggle_enharmonic_spelling(self):
        if self._enharmonic_mode == 'sharp':
            # Try switching to flat
            if self._flat_spelling is not None:
                self._enharmonic_mode = 'flat'
            elif self._sharp_spelling is None:
                # Both invalid, allow toggle
                self._enharmonic_mode = 'flat'
        else:
            # Try switching to sharp
            if self._sharp_spelling is not None:
                self._enharmonic_mode = 'sharp'
            elif self._flat_spelling is None:
                # Both invalid, allow toggle
                self._enharmonic_mode = 'sharp'
        
        self._update_final_names()
        self.updated.emit()

    def _get_sharp_names(self):
        return list(self.SHARP_NAMES)

    def _get_flat_names(self):
        return list(self.FLAT_NAMES)

    def _solve_spelling(self, active_set, use_sharps):
        naturals = self._NATURALS
        accidentals = self._SHARP_ACCIDENTALS if use_sharps else self._FLAT_ACCIDENTALS
            
        def solve(col_idx, notes_to_cover):
            if col_idx == 7:
                return [] if not notes_to_cover else None
            
            col_opts = []
            
            val_n, name_n = naturals[col_idx]
            if val_n in notes_to_cover:
                col_opts.append((val_n, name_n, False))
                
            val_a, name_a = accidentals[col_idx]
            if val_a in notes_to_cover:
                col_opts.append((val_a, name_a, True))
                
            for val, name, is_acc in col_opts:
                res = solve(col_idx + 1, notes_to_cover - {val})
                if res is not None:
                    return [(val, name, is_acc)] + res
            
            return None

        return solve(0, active_set)

    def _is_harmonic(self):
        mask = 2477
        shape = self._scale_model.shape
        for i in range(12):
            rotated = rotate(mask, i)
            if shape == rotated:
                return True, i
        return False, 0

    def _compute_spelling(self, use_sharps):
        active_set = set()
        mask = self._scale_model.number
        root = self._scale_model.root_note
        for i in range(12):
            if (mask >> i) & 1:
                active_set.add(i)

        is_harm, offset = self._is_harmonic()
        if is_harm:
            rel_target = (11 - offset) % 12
            abs_target = (rel_target + root) % 12
            abs_proxy = (abs_target - 1) % 12
            
            if abs_target in active_set:
                proxy_set = active_set.copy()
                proxy_set.remove(abs_target)
                proxy_set.add(abs_proxy)
                
                sol = self._solve_spelling(proxy_set, use_sharps)
                if sol:
                    names = self._get_sharp_names() if use_sharps else self._get_flat_names()
                    for val, name, _ in sol:
                        names[val] = name
                    
                    base_name = names[abs_proxy]
                    if base_name.endswith('♭'):
                        new_name = base_name[:-1] + "♮"
                    elif base_name.endswith('♯'):
                        new_name = base_name[:-1] + "𝄪"
                    else:
                        new_name = base_name + "♯"
                    names[abs_target] = new_name
                    return names

        sol = self._solve_spelling(active_set, use_sharps)
        if sol:
            names = self._get_sharp_names() if use_sharps else self._get_flat_names()
            for val, name, _ in sol:
                names[val] = name
            return names
            
        return None

    def _update_spellings(self):
        self._sharp_spelling = self._compute_spelling(True)
        self._flat_spelling = self._compute_spelling(False)
        
        # Determine mode
        if self._sharp_spelling and self._flat_spelling:
            def count_acc(names):
                c = 0
                for n in names:
                    if '♯' in n: c += 1
                    if '♭' in n: c += 1
                    if '𝄪' in n: c += 2
                return c

            s_count = count_acc(self._sharp_spelling)
            f_count = count_acc(self._flat_spelling)
            
            if f_count < s_count:
                self._enharmonic_mode = 'flat'
            elif s_count < f_count:
                self._enharmonic_mode = 'sharp'
            else:
                if self._scale_model.root_note in [1, 3, 5, 8, 10]:
                    self._enharmonic_mode = 'flat'
                else:
                    self._enharmonic_mode = 'sharp'
                    
        elif self._sharp_spelling:
            self._enharmonic_mode = 'sharp'
        elif self._flat_spelling:
            self._enharmonic_mode = 'flat'
        
        self._update_final_names()
        self.updated.emit()

    def _update_final_names(self):
        if self._enharmonic_mode == 'sharp':
            if self._sharp_spelling:
                self._note_names = self._sharp_spelling
            else:
                self._note_names = self._get_sharp_names()
        else:
            if self._flat_spelling:
                self._note_names = self._flat_spelling
            else:
                self._note_names = self._get_flat_names()