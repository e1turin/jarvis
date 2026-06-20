"""
Audio recording — captures microphone input with VAD or fixed duration.

Single responsibility: record audio from the microphone.
No STT, no wake word detection, no playback.
"""

from __future__ import annotations

import os
import numpy as np
import sounddevice as sd
from scipy.io import wavfile
from jarvis.config import settings


class Recorder:
    """
    Records audio from the microphone.
    Supports VAD (Voice Activity Detection) and fixed-duration modes.
    """

    def __init__(self):
        self.sample_rate = settings.audio_sample_rate
        self.max_wait = settings.listener_max_wait
        self.vad_mode = settings.vad_mode
        self.silence_timeout = settings.vad_silence_timeout
        self.vad_threshold = settings.vad_threshold
        self.temp_dir = settings.temp_dir

    def record(self) -> str:
        """
        Record audio from the microphone.
        Returns path to a WAV file, or empty string if no speech captured.
        """
        if self.vad_mode:
            return self._record_vad()
        return self._record_fixed()

    def _temp_path(self, name: str) -> str:
        return os.path.join(self.temp_dir, name)

    def _record_fixed(self) -> str:
        """Record for a fixed duration."""
        filename = self._temp_path("temp_audio.wav")
        duration = self.max_wait
        print(f"🎤 Listening for {duration}s...")
        recording = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
        )
        sd.wait()
        wavfile.write(filename, self.sample_rate, recording.flatten())
        return filename

    def _record_vad(self) -> str:
        """
        Record with voice activity detection.
        Starts when sound is detected, stops after silence_timeout of quiet.
        """
        filename = self._temp_path("temp_audio.wav")
        print(f"🎤 Listening (VAD, silence timeout: {self.silence_timeout}s)...")

        block_size = int(settings.vad_block_size_ms / 1000 * self.sample_rate)
        block_interval = settings.vad_block_size_ms / 1000.0
        threshold = self.vad_threshold

        audio_buffer: list[np.ndarray] = []
        speech_detected = False
        silence_frames = 0
        silence_limit = int(self.silence_timeout / block_interval)
        max_silent_blocks = int(self.max_wait / block_interval)
        total_blocks = 0

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                blocksize=block_size,
            ) as stream:
                while True:
                    block, _ = stream.read(block_size)
                    energy = np.sqrt(np.mean(block**2))

                    if energy > threshold:
                        if not speech_detected:
                            speech_detected = True
                            print("   🔴 Listening...")
                        silence_frames = 0
                        audio_buffer.append(block)
                    else:
                        if not speech_detected:
                            total_blocks += 1
                            if total_blocks >= max_silent_blocks:
                                print("   ⏱️ No speech detected")
                                break
                        else:
                            silence_frames += 1
                            if silence_frames >= silence_limit:
                                print("   ✅ Done")
                                break
                            audio_buffer.append(block)

        except KeyboardInterrupt:
            print("   ⏹️ Stopped")

        if not audio_buffer:
            if os.path.exists(filename):
                os.remove(filename)
            return filename

        recording = np.concatenate(audio_buffer)
        wavfile.write(filename, self.sample_rate, recording.flatten())
        return filename

    @staticmethod
    def prepend_audio(base_file: str, prepend_file: str) -> str:
        """
        Prepend audio from prepend_file to base_file (in-place on base_file).
        Returns base_file path.
        """
        if not os.path.exists(prepend_file) or not os.path.exists(base_file):
            if os.path.exists(prepend_file) and not os.path.exists(base_file):
                os.rename(prepend_file, base_file)
            return base_file

        pre_rate, pre_data = wavfile.read(prepend_file)
        base_rate, base_data = wavfile.read(base_file)

        # Use the same sample rate (should match)
        combined = np.concatenate([pre_data, base_data])
        wavfile.write(base_file, pre_rate, combined)

        os.remove(prepend_file)
        return base_file
