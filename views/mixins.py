from PySide6.QtCore import QPropertyAnimation, QEasingCurve, Property, QTimer
from PySide6.QtGui import QColor

class RotationAnimationMixin:
    """
    Mixin to provide rotation animation capabilities to a View.
    Expects the class to inherit from QObject/QWidget and have a 'scale_model' attribute.
    """
    def init_animation(self):
        self._anim_offset = float(self.scale_model.root_note)
        self.anim = QPropertyAnimation(self, b"animOffset")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.scale_model.updated.connect(self.on_model_update)

    def is_animating(self):
        return self.anim.state() == QPropertyAnimation.State.Running

    def get_anim_offset(self):
        return self._anim_offset

    def set_anim_offset(self, val):
        self._anim_offset = val
        self.update()

    animOffset = Property(float, get_anim_offset, set_anim_offset)

    def on_model_update(self):
        target = self.scale_model.root_note
        current = self._anim_offset
        
        diff = target - current
        
        # Shortest path logic for circular wrapping (0 <-> 11)
        if diff > 6:
            self._anim_offset += 12
        elif diff < -6:
            self._anim_offset -= 12
            
        self.anim.setStartValue(self._anim_offset)
        self.anim.setEndValue(target)
        self.anim.start()
        self.update()

class PlaybackHighlightMixin:
    """
    Mixin to provide visual highlighting when a note is played.
    """
    def init_highlight_animation(self):
        self._highlight_data = {}
        self._highlight_timer = QTimer(self)
        self._highlight_timer.setInterval(16)
        self._highlight_timer.timeout.connect(self._update_highlights)

    def highlight_note(self, note_val, duration):
        decay = 0.05
        
        self._highlight_data[note_val] = {
            'val': 0.0,
            'state': 'attack',
            'decay': decay
        }
        if not self._highlight_timer.isActive():
            self._highlight_timer.start()

    def _update_highlights(self):
        keys_to_remove = []
        
        for note, data in self._highlight_data.items():
            if data['state'] == 'attack':
                data['val'] += 0.25 # Fast attack (4 frames)
                if data['val'] >= 1.0:
                    data['val'] = 1.0
                    data['state'] = 'decay'
            elif data['state'] == 'decay':
                data['val'] -= data['decay']
                if data['val'] <= 0:
                    data['val'] = 0
                    keys_to_remove.append(note)
        
        for k in keys_to_remove:
            del self._highlight_data[k]
            
        if not self._highlight_data:
            self._highlight_timer.stop()
            
        self.update()

    def get_interpolated_color(self, note_val, base_color, target_color):
        val = self._highlight_data.get(note_val, {}).get('val', 0.0)
        if val <= 0: return base_color
        
        r = base_color.red() * (1 - val) + target_color.red() * val
        g = base_color.green() * (1 - val) + target_color.green() * val
        b = base_color.blue() * (1 - val) + target_color.blue() * val
        return QColor(int(r), int(g), int(b))