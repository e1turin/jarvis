import os
import numpy as np
import sounddevice as sd
from scipy.io import wavfile
from jarvis.config import settings


class Listener:
    def __init__(self, sample_rate: int = 16000, duration: int = 5):
        self.sample_rate = sample_rate
        self.duration = duration
        self.vad_mode = settings.vad_mode
        self.silence_timeout = settings.vad_silence_timeout
        self.vad_threshold = settings.vad_threshold

        if settings.llm_provider == "lmstudio":
            from faster_whisper import WhisperModel
            self.model = WhisperModel(settings.stt_model, device="cpu", compute_type="int8")
            self.transcriber = self._transcribe_local
        else:
            from openai import OpenAI
            self.client = OpenAI(
                base_url=settings.llm_base_url or None,
                api_key=settings.llm_api_key,
            )
            self.transcriber = self._transcribe_api

    def record_audio(self) -> str:
        if self.vad_mode:
            return self._record_vad()
        else:
            return self._record_fixed()

    def _record_fixed(self) -> str:
        """Record for a fixed duration."""
        filename = "temp_audio.wav"
        print(f"🎤 Listening for {self.duration} seconds...")
        recording = sd.rec(int(self.duration * self.sample_rate),
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

        # Use a small buffer and detect energy
        block_size = int(0.05 * self.sample_rate)  # 50ms blocks
        threshold = self.vad_threshold  # Energy threshold for voice activity
        block_interval = 0.05  # seconds per block

        audio_buffer = []
        speech_detected = False
        silence_frames = 0
        silence_limit = int(self.silence_timeout / block_interval)  # blocks of silence before stopping
        max_silent_blocks = int(self.duration / block_interval)  # total silent blocks before giving up
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
        return self.transcriber(audio_file)

    def _transcribe_api(self, audio_file: str) -> str:
        try:
            with open(audio_file, "rb") as f:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f
                )
            return transcript.text
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return ""

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
