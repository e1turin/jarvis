import os
import numpy as np
import sounddevice as sd
from scipy.io import wavfile
from jarvis.config import settings


class Listener:
    def __init__(self):
        self.sample_rate = settings.audio_sample_rate
        self.max_wait = settings.listener_max_wait
        self.vad_mode = settings.vad_mode
        self.silence_timeout = settings.vad_silence_timeout
        self.vad_threshold = settings.vad_threshold
        self._pre_wake_file = None

        # Always use local faster-whisper (offline, fast, independent of LLM)
        from faster_whisper import WhisperModel
        self.model = WhisperModel(settings.stt_model, device="cpu", compute_type="int8")

    def set_pre_wake(self, file_path: str | None):
        """Set a pre-wake buffer file to prepend to the next recording."""
        self._pre_wake_file = file_path

    def record_audio(self) -> str:
        if self.vad_mode:
            result = self._record_vad()
        else:
            result = self._record_fixed()

        # Prepend pre-wake buffer on first call after wake word
        if self._pre_wake_file and os.path.exists(self._pre_wake_file):
            result = self._prepend_pre_wake(result)
            self._pre_wake_file = None

        return result

    def _prepend_pre_wake(self, vad_file: str) -> str:
        """Prepend pre-wake audio to the VAD recording."""
        if not os.path.exists(vad_file) or os.path.getsize(vad_file) < 1000:
            # No VAD audio — use pre-wake as-is
            os.rename(self._pre_wake_file, vad_file)
            return vad_file

        pre_rate, pre_data = wavfile.read(self._pre_wake_file)
        vad_rate, vad_data = wavfile.read(vad_file)

        combined = np.concatenate([pre_data, vad_data])
        wavfile.write(vad_file, pre_rate, combined)

        os.remove(self._pre_wake_file)
        return vad_file

    def _record_fixed(self) -> str:
        """Record for a fixed duration."""
        filename = "temp_audio.wav"
        print(f"🎤 Listening for {self.max_wait} seconds...")
        recording = sd.rec(int(self.max_wait * self.sample_rate),
                           samplerate=self.sample_rate,
                           channels=1,
                           dtype='float32')
        sd.wait()
        wavfile.write(filename, self.sample_rate, recording.flatten())
        return filename

    def _record_vad(self) -> str:
        """
        Record with Voice Activity Detection.
        Starts recording when sound is detected, stops after silence_timeout seconds of quiet.
        If no speech is detected within `duration` seconds, returns empty.
        """
        filename = "temp_audio.wav"
        print(f"🎤 Listening (VAD, silence timeout: {self.silence_timeout}s)...")

        # Use configurable block size for energy detection
        block_size = int(settings.vad_block_size_ms / 1000 * self.sample_rate)
        block_interval = settings.vad_block_size_ms / 1000.0  # seconds per block
        threshold = self.vad_threshold

        audio_buffer = []
        speech_detected = False
        silence_frames = 0
        silence_limit = int(self.silence_timeout / block_interval)  # blocks of silence before stopping
        max_silent_blocks = int(self.max_wait / block_interval)  # total silent blocks before giving up
        total_blocks = 0

        try:
            with sd.InputStream(samplerate=self.sample_rate,
                                channels=1,
                                dtype='float32',
                                blocksize=block_size) as stream:
                while True:
                    block, _ = stream.read(block_size)
                    energy = np.sqrt(np.mean(block ** 2))

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
                            audio_buffer.append(block)  # keep a bit of silence

        except KeyboardInterrupt:
            print("   ⏹️ Stopped")

        if not audio_buffer:
            # No speech captured — remove stale audio to avoid re-transcribing old data
            if os.path.exists(filename):
                os.remove(filename)
            return filename

        recording = np.concatenate(audio_buffer)
        wavfile.write(filename, self.sample_rate, recording.flatten())
        return filename

    def transcribe(self, audio_file: str) -> str:
        if not os.path.exists(audio_file) or os.path.getsize(audio_file) < 1000:
            return ""
        print(f"📝 Transcribing...")
        return self._transcribe_local(audio_file)

    def _transcribe_local(self, audio_file: str) -> str:
        try:
            segments, _ = self.model.transcribe(audio_file)
            return "".join(seg.text for seg in segments)
        except Exception as e:
            print(f"❌ Local transcription error: {e}")
            return ""


if __name__ == "__main__":
    listener = Listener()
    file_path = listener.record_audio()
    text = listener.transcribe(file_path)
    print(f"📝 Transcribed: {text}")
