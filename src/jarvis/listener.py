import os
import numpy as np
import sounddevice as sd
from openai import OpenAI
from dotenv import load_dotenv
from scipy.io import wavfile
import time

load_dotenv()

class Listener:
    def __init__(self, sample_rate: int = 16000, duration: int = 5):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.sample_rate = sample_rate
        self.duration = duration

    def record_audio(self) -> str:
        """
        Records audio from the microphone and returns the path to the saved .wav file.
        """
        filename = "temp_audio.wav"
        print(f"Listening for {self.duration} seconds...")
        
        # Record audio
        recording = sd.rec(int(self.duration * self.sample_rate), 
                            samplerate=self.sample_rate, 
                            channels=1, 
                            dtype='float32')
        sd.wait()  # Wait until recording is finished
        
        # Save to file
        wavfile.write(filename, self.sample_rate, recording.flatten())
        return filename

    def transcribe(self, audio_file: str) -> str:
        """
        Transcribes the audio file using OpenAI Whisper.
        """
        try:
            with open(audio_file, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
            return transcript.text
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""

if __name__ == "__main__":
    # Quick test
    listener = Listener()
    file_path = listener.record_audio()
    text = listener.transcribe(file_path)
    print(f"Transcribed text: {text}")
