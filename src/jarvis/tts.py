"""
Text-to-Speech generation — produces audio files from text.

Single responsibility: generate audio files from text.
No playback, no cancellation — just generation.
Backends: edge (online), say (macOS), espeak (offline), yandex (online).
"""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
from jarvis.config import settings


class TTSGenerator:
    """
    Generates TTS audio files from text using the configured backend.
    No playback logic — returns file paths for the caller to play.
    """

    def __init__(self):
        self.temp_dir = settings.temp_dir

    def generate(self, text: str) -> str:
        """
        Generate TTS audio file and return the path.
        Returns empty string on failure or for 'print' backend.
        """
        backend = settings.tts_backend
        if backend == "edge":
            return self._generate_edge(text)
        elif backend == "yandex":
            return self._generate_yandex(text)
        elif backend == "say":
            return self._generate_say(text)
        elif backend == "espeak":
            return self._generate_espeak(text)
        elif backend == "print":
            return ""
        else:
            print(f"  Unknown TTS backend: {backend}, falling back to say")
            return self._generate_say(text)

    def _temp_path(self, name: str) -> str:
        return os.path.join(self.temp_dir, name)

    # ── Edge TTS (online, best quality) ────────────────────────

    def _generate_edge(self, text: str) -> str:
        try:
            import edge_tts

            file_path = self._temp_path("temp_response.mp3")
            proxy_url = settings.https_proxy or settings.http_proxy or None
            if proxy_url:
                communicate = edge_tts.Communicate(
                    text,
                    voice=settings.tts_voice,
                    rate=settings.tts_rate,
                    proxy=proxy_url,
                )
            else:
                communicate = edge_tts.Communicate(
                    text,
                    voice=settings.tts_voice,
                    rate=settings.tts_rate,
                )
            asyncio.run(communicate.save(file_path))
            return file_path
        except Exception as e:
            print(f"  TTS generation error: {e}")
            return ""

    # ── macOS say (offline, built-in) ──────────────────────────

    @staticmethod
    def _parse_say_rate(rate_str: str) -> int | None:
        """Convert percentage rate (+20%, -30%) to words-per-minute for say."""
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
        voice = settings.tts_voice or "Milena"
        rate = self._parse_say_rate(settings.tts_rate)
        file_path = self._temp_path("temp_response.aiff")
        try:
            cmd = ["say", "-o", file_path, "-v", voice]
            if rate is not None:
                cmd += ["-r", str(rate)]
            cmd += [text]
            proc = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            proc.wait(timeout=settings.tts_gen_timeout)
            if os.path.exists(file_path):
                return file_path
            return ""
        except subprocess.TimeoutExpired:
            print("  TTS generation timed out")
            proc.kill()
            proc.wait(timeout=2)
            return ""
        except Exception as e:
            print(f"  TTS generation error (say): {e}")
            print("  Tip: Install Russian voices in System Settings → Accessibility → Spoken Content")
            return ""

    # ── espeak-ng (offline, cross-platform) ────────────────────

    def _generate_espeak(self, text: str) -> str:
        if not shutil.which("espeak-ng"):
            print("  espeak-ng not found. Install it or use a different TTS backend.")
            return ""
        voice = settings.tts_voice or "ru"
        file_path = self._temp_path("temp_response.wav")
        try:
            proc = subprocess.Popen(
                ["espeak-ng", "-v", voice, "-w", file_path, "--", text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            proc.wait(timeout=settings.tts_gen_timeout)
            if os.path.exists(file_path):
                return file_path
            return ""
        except subprocess.TimeoutExpired:
            print("  TTS generation timed out")
            proc.kill()
            proc.wait(timeout=2)
            return ""
        except Exception as e:
            print(f"  TTS generation error (espeak-ng): {e}")
            return ""

    # ── Yandex SpeechKit (online, requires API key) ────────────

    def _generate_yandex(self, text: str) -> str:
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
            file_path = self._temp_path("temp_response.ogg")
            # Proxy auto-detected from HTTP_PROXY / HTTPS_PROXY env vars
            with httpx.Client() as client:
                response = client.post(url, headers=headers, data=data)
                response.raise_for_status()
                with open(file_path, "wb") as f:
                    f.write(response.content)
            return file_path
        except Exception as e:
            print(f"  Yandex TTS error: {e}")
            return ""
