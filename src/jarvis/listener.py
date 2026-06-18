import os
import numpy as np
import sounddevice as sd
from scipy.io import wavfile
from dotenv import load_dotenv

load_dotenv()


class Listener:
    def __init__(self, sample_rate: int = 16000, duration: int = 5):
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.sample_rate = sample_rate
        self.duration = duration
        self.vad_mode = os.getenv("VAD_MODE", "true").lower() == "true"
        self.silence_timeout = float(os.getenv("VAD_SILENCE_TIMEOUT", "1.5"))
        self.vad_threshold = float(os.getenv("VAD_THRESHOLD", "0.02"))

        if provider == "lmstudio":
            from faster_whisper import WhisperModel
            model_size = os.getenv("STT_MODEL", "base")
            self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
            self.transcriber = self._transcribe_local
        else:
            from openai import OpenAI
            base_url = os.getenv("LLM_BASE_URL")
            api_key = os.getenv("LLM_API_KEY")
            self.client = OpenAI(
                base_url=base_url,
                api_key=os.getenv("OPENAI_API_KEY") or api_key
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
        """
        filename = "temp_audio.wav"
        print(f"🎤 Listening (VAD, silence timeout: {self.silence_timeout}s)...")

        # Use a small buffer and detect energy
        block_size = int(0.05 * self.sample_rate)  # 50ms blocks
        threshold = self.vad_threshold  # Energy threshold for voice activity

        audio_buffer = []
        speech_detected = False
        silence_frames = 0
        silence_limit = int(self.silence_timeout / 0.05)  # blocks of silence before stopping

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
                        if speech_detected:
                            silence_frames += 1
                            if silence_frames >= silence_limit:
                                print("   ✅ Done")
                                break
                            audio_buffer.append(block)  # keep a bit of silence

        except KeyboardInterrupt:
            print("   ⏹️ Stopped")

        if not audio_buffer:
            return filename  # Return empty file

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
