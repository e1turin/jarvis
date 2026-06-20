import json
import os
from collections import deque
import numpy as np
import sounddevice as sd
from scipy.io import wavfile
from vosk import Model, KaldiRecognizer, SetLogLevel
from jarvis.config import settings

# Suppress verbose Vosk C++ LOG messages (they spam stderr on every load)
# -999 = absolutely everything off (word alignment warnings, etc.)
SetLogLevel(-999)

# Shared Vosk model instance (loaded once, reused by all detectors)
_VOSK_MODEL: Model | None = None


def _get_vosk_model() -> Model:
    global _VOSK_MODEL
    if _VOSK_MODEL is None:
        _VOSK_MODEL = Model(settings.vosk_model_path)
        wake_list = ", ".join(settings.wake_words)
        print(f"🔊 Vosk model loaded | Wake words: {wake_list}")
    return _VOSK_MODEL


class WakeWordDetector:
    def __init__(self):
        self.sample_rate = settings.audio_sample_rate
        self.model = _get_vosk_model()
        self.wake_words = settings.wake_words
        self.temp_dir = settings.temp_dir

        # Rolling buffer for pre-wake audio
        # blocksize=0.5s at sample_rate => 0.5s per block
        self._pre_buffer_blocks = int(settings.pre_wake_buffer_seconds / 0.5)
        self._pre_buffer = deque(maxlen=self._pre_buffer_blocks)
        self._pre_buffer_file = os.path.join(self.temp_dir, "temp_pre_wake.wav")

    def wait_for_wake_word(self) -> bool:
        """
        Wait until wake word is detected.
        Maintains a rolling buffer of audio so speech right before/during
        the wake word is preserved.
        Returns True when detected, False on Ctrl+C.
        """
        print(f"💤 Waiting... (say: {settings.wake_word_display})")
        print("   Press Ctrl+C to exit.")

        recognizer = KaldiRecognizer(self.model, self.sample_rate)
        recognizer.SetPartialWords(True)

        self._pre_buffer.clear()

        try:
            with sd.InputStream(samplerate=self.sample_rate,
                                channels=1,
                                dtype='int16',
                                blocksize=8000) as stream:
                while True:
                    block, _ = stream.read(8000)
                    # Keep a copy in the rolling buffer (stream reuses memory)
                    self._pre_buffer.append(block.copy())
                    data = block.tobytes()

                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        text = result.get("text", "").strip().lower()
                        if any(ww in text for ww in self.wake_words):
                            print("🔊 Wake word detected!")
                            self._save_pre_buffer()
                            return True
                    else:
                        partial = json.loads(recognizer.PartialResult())
                        text = partial.get("partial", "").strip().lower()
                        if any(ww in text for ww in self.wake_words):
                            print("🔊 Wake word detected!")
                            self._save_pre_buffer()
                            return True

        except KeyboardInterrupt:
            print("\nExiting...")
            return False

    def _save_pre_buffer(self):
        """Save the rolling audio buffer to a temp WAV file (float32)."""
        if not self._pre_buffer:
            return
        audio = np.concatenate(list(self._pre_buffer))
        # Convert int16 to float32 for consistency with VAD recordings
        audio_float = audio.astype(np.float32) / 32768.0
        wavfile.write(self._pre_buffer_file, self.sample_rate, audio_float)

    def get_pre_buffer_file(self) -> str | None:
        """Return path to pre-wake audio, or None if not available."""
        if os.path.exists(self._pre_buffer_file):
            return self._pre_buffer_file
        return None

    def clear_pre_buffer(self):
        """Delete the saved pre-wake buffer file."""
        self._pre_buffer.clear()
        if os.path.exists(self._pre_buffer_file):
            os.remove(self._pre_buffer_file)

    def wait_for_barge_in(self, is_playing) -> bool:
        """
        Listen for wake word while is_playing() returns True.
        Keeps stream open continuously. Returns True if interrupted, False if playback finished.
        """
        recognizer = KaldiRecognizer(self.model, self.sample_rate)
        recognizer.SetPartialWords(True)

        try:
            with sd.InputStream(samplerate=self.sample_rate,
                                channels=1,
                                dtype='int16',
                                blocksize=4000) as stream:
                while is_playing():
                    block, _ = stream.read(4000)
                    data = block.tobytes()

                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        text = result.get("text", "").strip().lower()
                        if any(ww in text for ww in self.wake_words):
                            return True
                    else:
                        partial = json.loads(recognizer.PartialResult())
                        text = partial.get("partial", "").strip().lower()
                        if any(ww in text for ww in self.wake_words):
                            return True
        except Exception as e:
            # Log barge-in errors but don't crash — treat as "not interrupted"
            import traceback
            traceback.print_exc()
        return False
