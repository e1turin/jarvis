import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from jarvis.config import settings


class WakeWordDetector:
    def __init__(self):
        self.sample_rate = 16000
        self.model = Model(settings.vosk_model_path)
        self.wake_words = settings.wake_words
        print(f"🔊 Vosk model loaded | Wake words: {', '.join(self.wake_words)}")

    def wait_for_wake_word(self) -> bool:
        """Wait until wake word is detected. Returns True when detected, False on Ctrl+C."""
        print("💤 Waiting... (say: Джарвис)")
        print("   Press Ctrl+C to exit.")

        recognizer = KaldiRecognizer(self.model, self.sample_rate)
        recognizer.SetWords(True)
        recognizer.SetPartialWords(True)

        try:
            with sd.InputStream(samplerate=self.sample_rate,
                                channels=1,
                                dtype='int16',
                                blocksize=8000) as stream:
                while True:
                    block, _ = stream.read(8000)
                    data = block.tobytes()

                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        text = result.get("text", "").strip().lower()
                        if any(ww in text for ww in self.wake_words):
                            print("🔊 Wake word detected!")
                            return True
                    else:
                        partial = json.loads(recognizer.PartialResult())
                        text = partial.get("partial", "").strip().lower()
                        if any(ww in text for ww in self.wake_words):
                            print("🔊 Wake word detected!")
                            return True

        except KeyboardInterrupt:
            print("\nExiting...")
            return False

    def wait_for_barge_in(self, is_playing) -> bool:
        """
        Listen for wake word while is_playing() returns True.
        Keeps stream open continuously. Returns True if interrupted, False if playback finished.
        """
        recognizer = KaldiRecognizer(self.model, self.sample_rate)
        recognizer.SetWords(True)
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
        except Exception:
            pass
        return False
