import os
import subprocess
import asyncio
import shutil
from jarvis.config import settings


class Speaker:
    def __init__(self):
        self.playback_process = None
        self.current_file = None
        self._gen_process = None
        self._cancelled = False

    def _cancel_gen(self):
        """Kill the TTS generation subprocess if running."""
        if self._gen_process and self._gen_process.poll() is None:
            self._gen_process.kill()
            try:
                self._gen_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass
            self._gen_process = None

    def generate_speech(self, text: str) -> str:
        """Generate TTS audio file and return the path. Blocks until done."""
        self._cancelled = False
        backend = settings.tts_backend
        if backend == "edge":
            return self._generate_edge(text)
        elif backend == "yandex":
            return self._generate_yandex(text)
        elif backend == "say":
            return self._generate_say(text)
        elif backend == "espeak":
            return self._generate_espeak(text)
        else:
            # Fallback: print only
            return ""

    def play_async(self, file_path: str):
        """Start playing audio in background. Returns immediately."""
        if not file_path or not os.path.exists(file_path):
            return
        try:
            if os.uname().sysname == "Darwin":
                self.playback_process = subprocess.Popen(["afplay", file_path])
            elif shutil.which("ffplay"):
                self.playback_process = subprocess.Popen(
                    ["ffplay", "-nodisp", "-autoexit", file_path],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            elif shutil.which("aplay"):
                self.playback_process = subprocess.Popen(["aplay", file_path])
            self.current_file = file_path
        except Exception as e:
            print(f"  Playback error: {e}")
            self.playback_process = None

    def stop_playback(self):
        """Stop TTS generation AND audio playback immediately."""
        self._cancelled = True
        self._cancel_gen()
        if self.playback_process and self.playback_process.poll() is None:
            self.playback_process.terminate()
            try:
                self.playback_process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.playback_process.kill()
            self.playback_process = None

    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        return (self.playback_process is not None and
                self.playback_process.poll() is None)

    def speak(self, text: str):
        """Simple blocking speak (for non-interrupted use)."""
        print(f"Jarvis: {text}")

        if settings.tts_backend == "print":
            return

        file_path = self.generate_speech(text)
        self.play_async(file_path)

        # Wait for playback to finish (blocking)
        if self.playback_process:
            self.playback_process.wait()

    def _generate_edge(self, text: str) -> str:
        """Generate speech using edge-tts, return file path."""
        try:
            import edge_tts
            file_path = "temp_response.mp3"
            asyncio.run(
                edge_tts.Communicate(text, voice=settings.tts_voice, rate=settings.tts_rate).save(file_path)
            )
            return file_path
        except Exception as e:
            print(f"  TTS generation error: {e}")
            return ""

    @staticmethod
    def _parse_say_rate(rate_str: str) -> int | None:
        """
        Convert edge-tts percentage rate (+0%, +20%, -30%) to
        words-per-minute for the `say` command (default ~200 wpm).
        Returns None to use say's default.
        """
        if not rate_str:
            return None
        rate_str = rate_str.strip()
        if rate_str.endswith("%"):
            try:
                percent = float(rate_str[:-1])
                base_rate = 200
                return max(50, int(round(base_rate * (1 + percent / 100))))
            except ValueError:
                return None
        return None

    def _generate_say(self, text: str) -> str:
        """
        Generate speech using macOS built-in `say` command.
        Fully offline. Voice must be installed in the system.
        Uses Popen so the process can be killed if interrupted.
        """
        voice = settings.tts_voice or "Milena"
        rate = self._parse_say_rate(settings.tts_rate)
        file_path = "temp_response.aiff"
        try:
            cmd = ["say", "-o", file_path, "-v", voice]
            if rate is not None:
                cmd += ["-r", str(rate)]
            cmd += [text]
            self._gen_process = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            self._gen_process.wait(timeout=settings.tts_gen_timeout)
            if os.path.exists(file_path):
                return file_path
            return ""
        except subprocess.TimeoutExpired:
            print("  TTS generation timed out")
            self._cancel_gen()
            return ""
        except Exception as e:
            print(f"  TTS generation error (say): {e}")
            print("  Tip: Install Russian voices in System Settings → Accessibility → Spoken Content")
            return ""

    def _generate_espeak(self, text: str) -> str:
        """
        Generate speech using espeak-ng (cross-platform, fully offline).
        Uses Popen so the process can be killed if interrupted.
        """
        if not shutil.which("espeak-ng"):
            print("  espeak-ng not found. Install it or use a different TTS backend.")
            return ""
        voice = settings.tts_voice or "ru"
        file_path = "temp_response.wav"
        try:
            self._gen_process = subprocess.Popen(
                ["espeak-ng", "-v", voice, "-w", file_path, "--", text],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            self._gen_process.wait(timeout=settings.tts_gen_timeout)
            if os.path.exists(file_path):
                return file_path
            return ""
        except subprocess.TimeoutExpired:
            print("  TTS generation timed out")
            self._cancel_gen()
            return ""
        except Exception as e:
            print(f"  TTS generation error (espeak-ng): {e}")
            return ""

    def _generate_yandex(self, text: str) -> str:
        """Generate speech using Yandex SpeechKit, return file path."""
        import httpx
        api_key = settings.yc_api_key
        folder_id = settings.yc_folder_id
        voice = settings.tts_voice or "alisa"
        lang = settings.tts_lang

        if not api_key or not folder_id:
            print("  Error: YC_API_KEY and YC_FOLDER_ID must be set in .env")
            return ""

        try:
            url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"
            headers = {"Authorization": f"Api-Key {api_key}"}

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
            return file_path

        except Exception as e:
            print(f"  Yandex TTS error: {e}")
            return ""
