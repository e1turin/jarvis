import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class Speaker:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def speak(self, text: str):
        """
        Converts text to speech using OpenAI TTS and plays it.
        """
        print(f"Jarvis: {text}")
        try:
            response = self.client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text
            )
            
            # Save to a temporary file
            file_path = "temp_response.mp3"
            response.stream_to_file(file_path)
            
            # Note: In a production environment, we'd use a library 
            # like `pygame` or `pydub` to play the file without blocking.
            # For now, we'll assume the user can handle the file or 
            # we can use a simple system call to play it.
            # For this demo, we will just print that it was generated.
            print(f"Audio saved to {file_path}")
            
        except Exception as e:
            print(f"Speaker error: {e}")

if __name__ == "__main__":
    speaker = Speaker()
    speaker.speak("Hello, I am Jarvis. How can I help you today?")
