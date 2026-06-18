import os
import subprocess
import asyncio
import shutil
from dotenv import load_dotenv

load_dotenv()


class Speaker:
    def __init__(self):
        backend = os.getenv("TTS_BACKEND", "edge").lower()
        self.backend = backend

        if backend == "yandex":
            self.speak_func = self._speak_yandex
        elif backend == "macos":
            self.speak_func = self._speak_macos
        elif backend == "print":
            self.speak_func = self._speak_print
        else:
            # Default: edge-tts
            self.speak_func = self._speak_edge

    def speak(self, text: str):
        self.speak_func(text)

    def _play_audio(self, file_path: str):
        """Play an audio file using system player."""
        if not os.path.exists(file_path):
            return
        try:
            if os.uname().sysname == "Darwin":
                subprocess.run(["afplay", file_path], check=True)
            else:
                # Try ffplay, then aplay as fallback
                if shutil.which("ffplay"):
                    subprocess.run(["ffplay", "-nodisp", "-autoexit", file_path],
                                   check=True, capture_output=True)
                elif shutil.which("aplay"):
                    subprocess.run(["aplay", file_path], check=True)
                else:
                    print(f"  (audio saved to {file_path})")
        except Exception as e:
            print(f"  Playback error: {e}")

    # ---------- Backend: edge-tts ----------
    def _speak_edge(self, text: str):
        print(f"Jarvis: {text}")
        try:
            import edge_tts
            voice = os.getenv("TTS_VOICE", "en-US-JennyNeural")
            file_path = "temp_response.mp3"
            asyncio.run(
                edge_tts.Communicate(text, voice=voice).save(file_path)
            )
            self._play_audio(file_path)
        except Exception as e:
            print(f"  TTS error: {e}")

    # ---------- Backend: Yandex SpeechKit ----------
    def _speak_yandex(self, text: str):
        print(f"Jarvis: {text}")
        import httpx

        api_key = os.getenv("YC_API_KEY") or os.getenv("YC_IAM_TOKEN")
        folder_id = os.getenv("YC_FOLDER_ID")
        voice = os.getenv("TTS_VOICE", "alisa")
        lang = os.getenv("TTS_LANG", "ru-RU")

        if not api_key or not folder_id:
            print("  Error: YC_API_KEY and YC_FOLDER_ID must be set in .env for Yandex TTS")
            return

        try:
            # Yandex SpeechKit v1 REST API
            url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"

            # Determine auth type
            if os.getenv("YC_API_KEY"):
                headers = {"Authorization": f"Api-Key {api_key}"}
            else:
                headers = {"Authorization": f"Bearer {api_key}"}

            data = {
                "text": text,
                "voice": voice,
                "emotion": "neutral",
                "speed": 1.0,
                "format": "oggopus",
                "lang": lang,
                "folderId": folder_id,
            }

            file_path = "temp_response.ogg"
            with httpx.Client() as client:
                response = client.post(url, headers=headers, data=data)
                response.raise_for_status()
                with open(file_path, "wb") as f:
                    f.write(response.content)

            self._play_audio(file_path)

        except Exception as e:
            print(f"  Yandex TTS error: {e}")

    # ---------- Backend: macOS say ----------
    def _speak_macos(self, text: str):
        print(f"Jarvis: {text}")
        try:
            voice = os.getenv("TTS_VOICE", "")
            if voice:
                subprocess.run(["say", "-v", voice, text], check=True)
            else:
                subprocess.run(["say", text], check=True)
        except Exception as e:
            print(f"  macOS TTS error: {e}")

    # ---------- Backend: print only ----------
    def _speak_print(self, text: str):
        print(f"Jarvis: {text}")


if __name__ == "__main__":
    speaker = Speaker()
    speaker.speak("Hello, I am Jarvis. How can I help you today?")
