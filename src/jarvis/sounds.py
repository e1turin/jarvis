"""
Audio feedback cues — listening beep, thinking ticks.
Generates WAV files on demand from configurable freq/duration/volume.
Supports vibro/haptic feedback via system beep on supported Macs.
"""

import os
import subprocess
import shutil
import threading
import time
import numpy as np
from scipy.io import wavfile
from jarvis.config import settings

SAMPLE_RATE = 22050

# ── Audio player selection (cross-platform) ─────────────
_PLAYER_BLOCKING = None
_PLAYER_ASYNC = None


def _detect_players():
    global _PLAYER_BLOCKING, _PLAYER_ASYNC
    if os.uname().sysname == "Darwin":
        # macOS: afplay (comes built-in)
        _PLAYER_BLOCKING = ["afplay"]
        _PLAYER_ASYNC = ["afplay"]
    elif shutil.which("ffplay"):
        # Linux with ffplay from ffmpeg
        _PLAYER_BLOCKING = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"]
        _PLAYER_ASYNC = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"]
    elif shutil.which("aplay"):
        # Linux with ALSA aplay
        _PLAYER_BLOCKING = ["aplay", "-q"]
        _PLAYER_ASYNC = ["aplay", "-q"]
    else:
        _PLAYER_BLOCKING = None
        _PLAYER_ASYNC = None


_detect_players()


def _generate_beep(freq: float, duration: float, volume: float) -> np.ndarray:
    """Generate a sine wave tone with fade in/out."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    tone = volume * np.sin(2 * np.pi * freq * t)
    fade = int(SAMPLE_RATE * min(duration * 0.1, 0.01))  # 10% or 10ms
    if fade > 0:
        tone[:fade] *= np.linspace(0, 1, fade)
        tone[-fade:] *= np.linspace(1, 0, fade)
    return tone


def _play_blocking(file_path: str):
    """Play a WAV file and wait for completion."""
    if not os.path.exists(file_path) or _PLAYER_BLOCKING is None:
        return
    try:
        subprocess.run(
            [*_PLAYER_BLOCKING, file_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def _play_async(file_path: str):
    """Play a WAV file (non-blocking)."""
    if not os.path.exists(file_path) or _PLAYER_ASYNC is None:
        return
    try:
        subprocess.Popen(
            [*_PLAYER_ASYNC, file_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def _write_beep(file_path: str, freq: float, duration: float, volume: float):
    """Generate and write a beep WAV file."""
    tone = _generate_beep(freq, duration, volume)
    wavfile.write(file_path, SAMPLE_RATE, (tone * 32767).astype(np.int16))


def _tick_feedback():
    """Play tick or trigger haptic/vibro if available."""
    if settings.tick_vibro:
        try:
            subprocess.Popen(
                ["osascript", "-e", "beep"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            _play_async("temp_tick.wav")
    else:
        _play_async("temp_tick.wav")


def play_listen_sound():
    """
    Short low beep indicating Jarvis is about to listen.
    Plays synchronously so the beep finishes before recording starts.
    """
    _write_beep(
        "temp_listen.wav",
        freq=settings.listen_beep_freq,
        duration=settings.listen_beep_duration,
        volume=settings.listen_beep_volume,
    )
    _play_blocking("temp_listen.wav")


def play_thinking_ticks():
    """Start ticking in background while LLM is thinking."""
    global _tick_thread
    stop_thinking_ticks()
    # Pre-generate tick with current settings
    _write_beep(
        "temp_tick.wav",
        freq=settings.tick_freq,
        duration=settings.tick_duration,
        volume=settings.tick_volume,
    )
    _tick_stop.clear()
    _tick_thread = threading.Thread(target=_tick_loop, daemon=True)
    _tick_thread.start()


def stop_thinking_ticks():
    """Stop the thinking ticks."""
    _tick_stop.set()
    global _tick_thread
    if _tick_thread and _tick_thread.is_alive():
        _tick_thread.join(timeout=0.5)
    _tick_thread = None


def _tick_loop():
    """Play a tick periodically until told to stop."""
    while not _tick_stop.is_set():
        _tick_feedback()
        _tick_stop.wait(settings.tick_interval)


# Module-level state for the tick thread
_tick_thread: threading.Thread | None = None
_tick_stop = threading.Event()
