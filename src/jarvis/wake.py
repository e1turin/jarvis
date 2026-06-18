import os
import json
import numpy as np
import sounddevice as sd
from dotenv import load_dotenv
from vosk import Model, KaldiRecognizer

load_dotenv()


class WakeWordDetector:
    def __init__(self):
        self.sample_rate = 16000

        # Load Vosk model
        model_path = os.getenv("VOSK_MODEL_PATH", "vosk-model-small-ru-0.22")
        self.model = Model(model_path)

        # Wake words to listen for
        wake_words_str = os.getenv("WAKE_WORDS", "джарвис")
        self.wake_words = [w.strip().lower() for w in wake_words_str.split(",")]

        print(f"🔊 Vosk model loaded | Wake words: {', '.join(self.wake_words)}")

    def wait_for_wake_word(self) -> bool:
        """
        Listen continuously and detect wake word in Vosk transcription.
        Checks both partial and final results for the wake word.
        """
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
                            print(f"🔊 Wake word detected!")
                            return True
                    else:
                        partial = json.loads(recognizer.PartialResult())
                        text = partial.get("partial", "").strip().lower()
                        if any(ww in text for ww in self.wake_words):
                            print(f"🔊 Wake word detected!")
                            return True

        except KeyboardInterrupt:
            print("\nExiting...")
            return False
