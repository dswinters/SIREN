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
        self._instrument = "Guitar"
        self._sample_rate = 44100
        self._root_offset = 0
        self._mask = []

    @property
    def is_playing(self):
        return self._thread is not None and self._thread.is_alive()

    def get_available_instruments(self):
        return ["Guitar", "Violin", "Piano"]

    def set_instrument(self, name):
        if name in self.get_available_instruments():
            self._instrument = name

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

    def _karplus_strong(self, frequency, duration):
        sample_rate = self._sample_rate
        N = int(sample_rate / frequency)
        if N <= 0:
            return np.zeros(int(sample_rate * duration), dtype=np.float32)
        
        n_samples = int(sample_rate * duration)
        
        # Initialize buffer based on instrument
        if self._instrument == "Guitar":
            buf = np.random.uniform(-1, 1, N)
            alpha = 0.996
        elif self._instrument == "Violin":
            # Sawtooth-like init for brighter tone, high feedback for sustain
            buf = np.linspace(-1, 1, N)
            alpha = 0.999
        elif self._instrument == "Piano":
            # White noise with slight smoothing
            buf = np.random.uniform(-1, 1, N)
            if N > 2:
                buf = 0.5 * buf + 0.25 * np.roll(buf, 1) + 0.25 * np.roll(buf, -1)
            alpha = 0.992
        else:
            buf = np.random.uniform(-1, 1, N)
            alpha = 0.99
        
        output = np.zeros(n_samples, dtype=np.float32)
        output[:N] = buf
        
        prev_block = buf
        cursor = N
        last_val = 0.0
        
        while cursor < n_samples:
            shifted = np.empty_like(prev_block)
            shifted[0] = last_val
            shifted[1:] = prev_block[:-1]
            
            next_block = alpha * 0.5 * (prev_block + shifted)
            last_val = prev_block[-1]
            
            take = min(len(next_block), n_samples - cursor)
            output[cursor:cursor+take] = next_block[:take]
            
            prev_block = next_block
            cursor += take
            
        # Simple release envelope
        release_len = int(0.05 * sample_rate)
        if n_samples > release_len:
            envelope = np.ones(n_samples, dtype=np.float32)
            envelope[-release_len:] = np.linspace(1, 0, release_len)
            output *= envelope
            
        return (output * 0.5).astype(np.float32)

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
                        audio_data = self._karplus_strong(freq, duration)
                        sd.play(audio_data, self._sample_rate, blocking=True)
                    except Exception as e:
                        print(f"Playback error: {e}")
                else:
                    time.sleep(duration)
            
            if not self._looping:
                break
        
        if not self._stop_event.is_set():
            self.playback_stopped.emit()