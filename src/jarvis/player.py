"""
Audio playback — plays audio files using system commands.

Single responsibility: play audio files, control playback.
No TTS generation — just play what it's given.
Supports cancellable playback and volume control (macOS afplay).
"""

from __future__ import annotations

import os
import shutil
import subprocess
from jarvis.config import settings


class Player:
    """
    Plays audio files using system commands.
    Supports macOS (afplay), Linux (ffplay or aplay).
    Playback can be stopped at any time (cancellable).
    """

    def __init__(self):
        self._playback_process: subprocess.Popen | None = None
        self.current_file: str | None = None

    def play(self, file_path: str):
        """
        Start playing audio in the background. Returns immediately.
        """
        if not file_path or not os.path.exists(file_path):
            return
        try:
            if os.uname().sysname == "Darwin":
                cmd = ["afplay", file_path]
                vol = settings.tts_volume
                if 0.0 <= vol < 1.0:
                    cmd += ["--volume", str(vol)]
                self._playback_process = subprocess.Popen(cmd)
            elif shutil.which("ffplay"):
                self._playback_process = subprocess.Popen(
                    ["ffplay", "-nodisp", "-autoexit", file_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif shutil.which("aplay"):
                self._playback_process = subprocess.Popen(["aplay", file_path])
            self.current_file = file_path
        except Exception as e:
            print(f"  Playback error: {e}")
            self._playback_process = None

    def stop(self):
        """Stop playback immediately."""
        if self._playback_process and self._playback_process.poll() is None:
            self._playback_process.terminate()
            try:
                self._playback_process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self._playback_process.kill()
            self._playback_process = None

    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        return (
            self._playback_process is not None
            and self._playback_process.poll() is None
        )

    def wait(self):
        """Block until playback finishes."""
        if self._playback_process:
            try:
                self._playback_process.wait()
            except Exception:
                pass
