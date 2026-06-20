"""
Listener — thin facade combining Recorder + STT + pre-wake buffer.

Kept for backward compatibility with main.py.
Delegates to recorder.py (audio capture) and stt.py (transcription).
"""

from __future__ import annotations

import os
from jarvis.recorder import Recorder
from jarvis.stt import STT
from jarvis.config import settings


class Listener:
    """
    Combines audio recording and speech-to-text.
    Also handles pre-wake buffer prepending.
    """

    def __init__(self):
        self.recorder = Recorder()
        self.stt = STT()
        self._pre_wake_file: str | None = None

    def set_pre_wake(self, file_path: str | None):
        """Set a pre-wake buffer file to prepend to the next recording."""
        self._pre_wake_file = file_path

    def record_audio(self) -> str:
        """Record audio and prepend pre-wake buffer if available."""
        result = self.recorder.record()

        # Prepend pre-wake buffer on first call after wake word
        if self._pre_wake_file and os.path.exists(self._pre_wake_file):
            result = Recorder.prepend_audio(result, self._pre_wake_file)
            self._pre_wake_file = None

        return result

    def transcribe(self, audio_file: str) -> str:
        """Transcribe audio file to text."""
        return self.stt.transcribe(audio_file)
