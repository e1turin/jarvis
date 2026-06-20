"""
Speech-to-text — transcribes audio files using faster-whisper (local, offline).

Single responsibility: transcribe audio → text.
No recording, no VAD, no wake word detection.
"""

from __future__ import annotations

import os
from faster_whisper import WhisperModel
from jarvis.config import settings


class STT:
    """
    Local speech-to-text using faster-whisper.
    Fully offline. No API calls.
    """

    def __init__(self):
        self.model = WhisperModel(
            settings.stt_model,
            device=settings.stt_device,
            compute_type=settings.stt_compute_type,
        )

    def transcribe(self, audio_file: str) -> str:
        """
        Transcribe a WAV audio file to text.
        Returns empty string if file is missing, empty, or on error.
        """
        if not audio_file or not os.path.exists(audio_file):
            return ""
        if os.path.getsize(audio_file) < 1000:
            return ""

        print("📝 Transcribing...")
        try:
            segments, _ = self.model.transcribe(audio_file)
            return "".join(seg.text for seg in segments)
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return ""
