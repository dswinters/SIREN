import time
import threading
import numpy as np
from PySide6.QtCore import QObject, Signal
from typing import List, Optional

try:
    import sounddevice as sd
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False
    print("Warning: sounddevice not found. Audio features disabled.")

class SoundEngine(QObject):
    playback_stopped = Signal()
    note_played = Signal(int, float)

    def __init__(self):
        super().__init__()
        self._thread = None
        self._stop_event = threading.Event()
        self._bpm = 120
        self._looping = False
        self._instrument = "Guitar"
        self._sample_rate = 44100
        self._root_note = 0
        self._value = 0
        self._octave_shift = 0

    @property
    def is_playing(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def get_available_instruments(self) -> List[str]:
        return ["Guitar", "Violin", "Piano"]

    def set_instrument(self, name: str):
        if name in self.get_available_instruments():
            self._instrument = name

    def set_bpm(self, bpm):
        try:
            val = int(bpm)
            if val > 0: self._bpm = val
        except ValueError:
            pass

    def set_looping(self, enabled: bool):
        self._looping = enabled

    def change_octave(self, delta: int):
        self._octave_shift += delta

    def update_scale(self, root_note: int, value: int):
        self._root_note = root_note
        self._value = value

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

    def _karplus_strong(self, frequency: float, duration: float) -> np.ndarray:
        sample_rate = self._sample_rate
        n_samples = int(sample_rate * duration)
        
        # Inner function to generate a single string's audio
        def generate_string(freq, decay, init_mode):
            N = int(sample_rate / freq)
            if N <= 0: return np.zeros(n_samples, dtype=np.float32)
            
            # Excitation
            if init_mode == "sawtooth":
                # Violin-like: rich harmonics
                buf = np.linspace(-1, 1, N, dtype=np.float32)
            elif init_mode == "smooth_noise":
                # Piano-like: softer attack (low-pass filtered noise)
                noise = np.random.uniform(-1, 1, N).astype(np.float32)
                buf = np.zeros_like(noise)
                if N > 1:
                    buf[1:] = 0.5 * (noise[1:] + noise[:-1])
                    buf[0] = noise[0]
                else:
                    buf = noise
            else:
                # Guitar-like: sharp attack (white noise)
                buf = np.random.uniform(-1, 1, N).astype(np.float32)

            output = np.zeros(n_samples, dtype=np.float32)
            output[:N] = buf
            
            # KS Loop
            prev_block = buf
            cursor = N
            last_val = 0.0 # Represents y[n-N-1] for the first sample of the block
            
            while cursor < n_samples:
                # Create y[n-N-1] vector
                delayed = np.empty_like(prev_block)
                delayed[0] = last_val
                delayed[1:] = prev_block[:-1]
                
                # Update last_val for the next block (it's the last value of the current prev_block)
                last_val = prev_block[-1]
                
                # Average and decay
                # y[n] = decay * 0.5 * (y[n-N] + y[n-N-1])
                current_block = decay * 0.5 * (prev_block + delayed)
                
                # Write to output
                take = min(len(current_block), n_samples - cursor)
                output[cursor:cursor+take] = current_block[:take]
                
                prev_block = current_block
                cursor += take
                
            return output

        # Instrument Logic
        if self._instrument == "Guitar":
            # Standard KS
            audio = generate_string(frequency, 0.996, "noise")
            
        elif self._instrument == "Violin":
            # High sustain, sawtooth init, slow attack
            audio = generate_string(frequency, 0.999, "sawtooth")
            # Apply fade-in (attack)
            attack_samples = int(0.1 * sample_rate)
            if n_samples > attack_samples:
                envelope = np.ones(n_samples, dtype=np.float32)
                envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
                audio *= envelope
                
        elif self._instrument == "Piano":
            # Two strings, slightly detuned, smoother noise
            s1 = generate_string(frequency, 0.995, "smooth_noise")
            s2 = generate_string(frequency * 1.003, 0.995, "smooth_noise")
            audio = 0.5 * (s1 + s2)
            
        else:
            audio = generate_string(frequency, 0.99, "noise")

        # Global Release Envelope (to prevent clicking at end of duration)
        release_len = int(0.05 * sample_rate)
        if n_samples > release_len:
            envelope = np.ones(n_samples, dtype=np.float32)
            envelope[-release_len:] = np.linspace(1, 0, release_len)
            audio *= envelope
            
        return audio

    def _run_playback(self):
        while not self._stop_event.is_set():
            # Construct sequence dynamically based on current state
            base_note = 60 + self._root_note
            sequence = []
            for i in range(12):
                if (self._value >> i) & 1:
                    sequence.append(base_note + i)
            
            if not sequence:
                self.playback_stopped.emit()
                return

            # Append the first note one octave higher
            sequence.append(sequence[0] + 12)

            for note in sequence:
                if self._stop_event.is_set(): break
                
                duration = 60.0 / self._bpm
                self.note_played.emit(note % 12, duration)
                
                if HAS_AUDIO:
                    try:
                        freq = 440.0 * (2 ** ((note + (self._octave_shift * 12) - 69) / 12.0))
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