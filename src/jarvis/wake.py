import os
import time
import numpy as np
import sounddevice as sd
from dotenv import load_dotenv

load_dotenv()


class WakeWordDetector:
    def __init__(self):
        self.sample_rate = 16000
        self.chunk_duration = 2.0  # seconds of audio to transcribe at a time
        self.chunk_samples = int(self.chunk_duration * self.sample_rate)
        self.hop_duration = 0.5  # check every 0.5 seconds
        self.hop_samples = int(self.hop_duration * self.sample_rate)

        # Load the tiny whisper model (fastest)
        from faster_whisper import WhisperModel
        self.model = WhisperModel("tiny", device="cpu", compute_type="int8")

        # Wake words to listen for (lowercase)
        wake_words_str = os.getenv("WAKE_WORDS", "jarvis,джарвис,жарвис")
        self.wake_words = [w.strip().lower() for w in wake_words_str.split(",")]

        # Audio ring buffer to keep the last N seconds
        buffer_duration = 3.0
        buffer_samples = int(buffer_duration * self.sample_rate)
        self.buffer = np.zeros(buffer_samples, dtype=np.float32)
        self.buffer_pos = 0

        print(f"🔊 Wake words: {', '.join(self.wake_words)}")

    def _add_to_buffer(self, audio_chunk: np.ndarray):
        """Add audio chunk to ring buffer."""
        n = len(audio_chunk)
        if n >= len(self.buffer):
            self.buffer = audio_chunk[-len(self.buffer):]
            self.buffer_pos = 0
        else:
            end = self.buffer_pos + n
            if end <= len(self.buffer):
                self.buffer[self.buffer_pos:end] = audio_chunk
            else:
                # Wrap around
                first_part = len(self.buffer) - self.buffer_pos
                self.buffer[self.buffer_pos:] = audio_chunk[:first_part]
                self.buffer[:n - first_part] = audio_chunk[first_part:]
            self.buffer_pos = (self.buffer_pos + n) % len(self.buffer)

    def _get_recent(self, duration_seconds: float) -> np.ndarray:
        """Get the most recent audio from the buffer."""
        n_samples = int(duration_seconds * self.sample_rate)
        if n_samples > len(self.buffer):
            n_samples = len(self.buffer)

        if self.buffer_pos >= n_samples:
            return self.buffer[self.buffer_pos - n_samples:self.buffer_pos]
        else:
            # Wrapped around, need to concatenate
            return np.concatenate([
                self.buffer[-(n_samples - self.buffer_pos):],
                self.buffer[:self.buffer_pos]
            ])

    def wait_for_wake_word(self) -> bool:
        """
        Continuously listen and check for wake word.
        Returns True when wake word is detected.
        """
        print("💤 Waiting for wake word... (say: Jarvis / Джарвис)")
        print("   Press Ctrl+C to exit.")

        # Reset buffer
        self.buffer.fill(0)
        self.buffer_pos = 0

        # For tracking consecutive detections (reduce false positives)
        detection_count = 0
        required_detections = 2  # Need 2 consecutive detections to confirm

        try:
            with sd.InputStream(samplerate=self.sample_rate,
                                channels=1,
                                dtype='float32',
                                blocksize=self.hop_samples) as stream:
                while True:
                    block, _ = stream.read(self.hop_samples)
                    self._add_to_buffer(block.flatten())

                    # Every N hops, grab the last chunk_duration seconds and transcribe
                    recent = self._get_recent(self.chunk_duration)
                    text = self._transcribe(recent)

                    if text:
                        text_lower = text.lower().strip()
                        # Check if any wake word is in the transcribed text
                        if any(ww in text_lower for ww in self.wake_words):
                            detection_count += 1
                            if detection_count >= required_detections:
                                print(f"\r🔊 Wake word detected! (\"{text.strip()}\")")
                                return True
                        else:
                            detection_count = max(0, detection_count - 1)

                    # Small delay to avoid CPU spinning
                    time.sleep(0.05)

        except KeyboardInterrupt:
            print("\nExiting...")
            return False

    def _transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio chunk and return the text."""
        try:
            # Normalize audio
            audio = audio / (np.max(np.abs(audio)) + 1e-10)
            segments, _ = self.model.transcribe(audio, beam_size=1, language="ru")
            return "".join(seg.text for seg in segments)
        except Exception:
            return ""


if __name__ == "__main__":
    detector = WakeWordDetector()
    while True:
        detected = detector.wait_for_wake_word()
        if detected:
            print("Wake word confirmed! Entering conversation mode.")
            # In real use, the main loop would take over here
        else:
            break
