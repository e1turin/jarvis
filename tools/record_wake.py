"""
Record a short sample and test wake word detection.

Use this to test how well Vosk hears your wake word and to tune
microphone placement, VAD_THRESHOLD, or your pronunciation.

Usage:
    uv run python tools/record_wake.py
    uv run python tools/record_wake.py --duration 5
"""

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import sounddevice as sd
from scipy.io import wavfile
from vosk import Model, KaldiRecognizer

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv

load_dotenv()

SAMPLE_RATE = 16000


def main():
    parser = argparse.ArgumentParser(description="Record a sample and test wake word detection")
    parser.add_argument("--duration", type=float, default=3.0, help="Recording duration in seconds")
    args = parser.parse_args()

    wake_words_str = os.getenv("WAKE_WORDS", "джарвис")
    wake_words = [w.strip().lower() for w in wake_words_str.split(",")]
    model_path = os.getenv("VOSK_MODEL_PATH", "vosk-model-small-ru-0.22")

    print(f"🔊 Loading Vosk model from: {model_path}")
    if not os.path.isdir(model_path):
        print(f"❌ Model directory not found: {model_path}")
        print("   Download from: https://alphacephei.com/vosk/models")
        sys.exit(1)

    model = Model(model_path)
    print(f"✅ Vosk model loaded")
    print(f"🎯 Wake words: {', '.join(wake_words)}")
    print(f"🎤 Recording {args.duration}s... Speak the wake word!")

    recording = sd.rec(int(args.duration * SAMPLE_RATE),
                       samplerate=SAMPLE_RATE,
                       channels=1,
                       dtype='int16')
    sd.wait()

    print("✅ Recording done. Testing detection...")

    # Save to recordings/
    records_dir = Path("recordings")
    records_dir.mkdir(exist_ok=True)
    out_path = records_dir / "test_sample.wav"
    wavfile.write(out_path, SAMPLE_RATE, recording.flatten())
    print(f"💾 Saved to: {out_path}")

    # Test detection
    recognizer = KaldiRecognizer(model, SAMPLE_RATE)
    recognizer.SetWords(True)
    recognizer.SetPartialWords(True)

    data = recording.tobytes()
    if recognizer.AcceptWaveform(data):
        result = json.loads(recognizer.Result())
        text = result.get("text", "").strip().lower()
    else:
        partial = json.loads(recognizer.PartialResult())
        text = partial.get("partial", "").strip().lower()

    print(f"📝 Recognized text: \"{text}\"")

    if any(ww in text for ww in wake_words):
        print(f"✅ ✅ ✅ WAKE WORD DETECTED! ✅ ✅ ✅")
        return 0
    else:
        print(f"❌ Wake word NOT detected")
        print("   Tips:")
        print("   - Speak clearly and at a natural pace")
        print("   - Check microphone permissions in System Settings → Privacy → Microphone")
        print("   - Try lowering VAD_THRESHOLD in .env (currently: {})".format(
            os.getenv("VAD_THRESHOLD", "0.02")))
        return 1


if __name__ == "__main__":
    sys.exit(main())
