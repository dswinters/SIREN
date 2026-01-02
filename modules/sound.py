import time
import threading
import numpy as np
from PySide6.QtCore import QObject, Signal

try:
    import sounddevice as sd
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False
    print("Warning: sounddevice not found. Audio features disabled.")

class SoundEngine(QObject):
    playback_stopped = Signal()

    def __init__(self):
        super().__init__()
        self._thread = None
        self._stop_event = threading.Event()
        self._bpm = 120
        self._looping = False
        self._waveform = "Sine"
        self._sample_rate = 44100
        self._root_offset = 0
        self._mask = []

    @property
    def is_playing(self):
        return self._thread is not None and self._thread.is_alive()

    def get_available_waveforms(self):
        return ["Sine", "Square", "Sawtooth", "Triangle"]

    def set_waveform(self, name):
        if name in self.get_available_waveforms():
            self._waveform = name

    def set_bpm(self, bpm):
        try:
            val = int(bpm)
            if val > 0: self._bpm = val
        except ValueError:
            pass

    def set_looping(self, enabled):
        self._looping = enabled

    def update_scale(self, root_offset, mask):
        self._root_offset = root_offset
        self._mask = mask

    def play(self):
        self.stop()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_playback)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join()
        self._thread = None
        self.playback_stopped.emit()

    def _generate_tone(self, frequency, duration):
        t = np.linspace(0, duration, int(self._sample_rate * duration), False)
        
        if self._waveform == "Sine":
            audio = np.sin(2 * np.pi * frequency * t)
        elif self._waveform == "Square":
            audio = np.sign(np.sin(2 * np.pi * frequency * t))
        elif self._waveform == "Sawtooth":
             audio = 2 * (t * frequency - np.floor(t * frequency + 0.5))
        elif self._waveform == "Triangle":
             audio = 2 * np.abs(2 * (t * frequency - np.floor(t * frequency + 0.5))) - 1
        else:
            audio = np.sin(2 * np.pi * frequency * t)

        # Apply a simple envelope to avoid clicking
        envelope = np.ones_like(audio)
        attack = int(0.01 * self._sample_rate)
        release = int(0.05 * self._sample_rate)
        
        if len(audio) > attack + release:
            envelope[:attack] = np.linspace(0, 1, attack)
            envelope[-release:] = np.linspace(1, 0, release)
        else:
            # Very short note, just window it
            envelope = np.hanning(len(audio))
            
        # Scale amplitude to prevent clipping
        return (audio * envelope * 0.3).astype(np.float32)

    def _run_playback(self):
        while not self._stop_event.is_set():
            # Construct sequence dynamically based on current state
            base_note = 60 + self._root_offset
            sequence = []
            for i, active in enumerate(self._mask):
                if active:
                    sequence.append(base_note + i)
            
            if not sequence:
                self.playback_stopped.emit()
                return

            # Append the first note one octave higher
            sequence.append(sequence[0] + 12)

            for note in sequence:
                if self._stop_event.is_set(): break
                
                duration = 60.0 / self._bpm
                
                if HAS_AUDIO:
                    try:
                        freq = 440.0 * (2 ** ((note - 69) / 12.0))
                        audio_data = self._generate_tone(freq, duration)
                        sd.play(audio_data, self._sample_rate, blocking=True)
                    except Exception as e:
                        print(f"Playback error: {e}")
                else:
                    time.sleep(duration)
            
            if not self._looping:
                break
        
        if not self._stop_event.is_set():
            self.playback_stopped.emit()