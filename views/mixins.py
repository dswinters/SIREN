from PySide6.QtCore import QPropertyAnimation, QEasingCurve, Property

class RotationAnimationMixin:
    """
    Mixin to provide rotation animation capabilities to a View.
    Expects the class to inherit from QObject/QWidget and have a 'scale_model' attribute.
    """
    def init_animation(self):
        self._anim_offset = float(self.scale_model.rotation_offset)
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
        target = self.scale_model.rotation_offset
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