"""
Speaker — thin facade combining TTS generation + audio playback.

Kept for backward compatibility with main.py.
Delegates to tts.py (generation) and player.py (playback).
"""

from __future__ import annotations

from jarvis.tts import TTSGenerator
from jarvis.player import Player
from jarvis.config import settings


class Speaker:
    """
    Combines TTS generation and audio playback.
    Supports cancellable generation + playback for barge-in.
    """

    def __init__(self):
        self.tts = TTSGenerator()
        self.player = Player()
        self._cancelled = False

    def generate_speech(self, text: str) -> str:
        """Generate TTS audio file and return the path. Blocks until done."""
        self._cancelled = False
        return self.tts.generate(text)

    def play_async(self, file_path: str):
        """Start playing audio in background. Returns immediately."""
        self.player.play(file_path)

    def stop_playback(self):
        """Stop generation AND playback immediately."""
        self._cancelled = True
        self.player.stop()

    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        return self.player.is_playing()

    def speak(self, text: str):
        """
        Simple blocking speak (for non-interrupted use like sleep responses).
        Generates and plays, waiting for playback to finish.
        """
        if settings.tts_backend == "print":
            return
        file_path = self.generate_speech(text)
        self.play_async(file_path)
        self.player.wait()
