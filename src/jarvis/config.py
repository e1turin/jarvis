"""
Centralized configuration — loads env vars once and provides typed access.
All other modules import `settings` from here instead of calling os.getenv directly.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    # --- LLM ---
    llm_provider: str = "lmstudio"
    llm_base_url: str = "localhost:1234/v1"
    llm_api_key: str = ""
    llm_model: str = "google/gemma-4-12b-qat"

    # --- STT ---
    stt_model: str = "base"

    # --- VAD ---
    vad_mode: bool = True
    vad_silence_timeout: float = 1.5
    vad_threshold: float = 0.02

    # --- TTS (Edge) ---
    tts_backend: str = "edge"
    tts_voice: str = "ru-RU-SvetlanaNeural"

    # --- TTS (Yandex) ---
    yc_api_key: str = ""
    yc_folder_id: str = ""
    tts_lang: str = "ru-RU"

    # --- Wake word ---
    wake_mode: bool = True
    wake_words: list[str] = field(default_factory=lambda: ["джарвис"])
    vosk_model_path: str = "vosk-model-small-ru-0.22"

    # --- Conversation ---
    conversation_timeout: int = 30

    # --- Sound feedback ---
    tick_vibro: bool = False
    listen_beep_freq: float = 200
    listen_beep_duration: float = 0.2
    listen_beep_volume: float = 0.4
    tick_freq: float = 350
    tick_duration: float = 0.03
    tick_volume: float = 0.15
    tick_interval: float = 2.0

    # --- System prompt ---
    system_prompt_path: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        def _bool(key: str, default: str = "false") -> bool:
            return os.getenv(key, default).lower() in ("true", "1", "yes")

        wake_words_raw = os.getenv("WAKE_WORDS", "джарвис")
        wake_words = [w.strip().lower() for w in wake_words_raw.split(",")]

        # Default prompt path: next to this file
        default_prompt = str(Path(__file__).parent / "prompt.txt")

        return cls(
            llm_provider=os.getenv("LLM_PROVIDER", "undefined"),
            llm_base_url=os.getenv("LLM_BASE_URL", ""),
            llm_api_key=os.getenv("LLM_API_KEY", ""),
            llm_model=os.getenv("LLM_MODEL", "undefined"),

            stt_model=os.getenv("STT_MODEL", "base"),
            vad_mode=_bool("VAD_MODE", "true"),
            vad_silence_timeout=float(os.getenv("VAD_SILENCE_TIMEOUT", "1.5")),
            vad_threshold=float(os.getenv("VAD_THRESHOLD", "0.02")),
            tts_backend=os.getenv("TTS_BACKEND", "edge").lower(),
            tts_voice=os.getenv("TTS_VOICE", "ru-RU-SvetlanaNeural"),
            yc_api_key=os.getenv("YC_API_KEY", ""),
            yc_folder_id=os.getenv("YC_FOLDER_ID", ""),
            tts_lang=os.getenv("TTS_LANG", "ru-RU"),
            wake_mode=_bool("WAKE_MODE", "true"),
            wake_words=wake_words,
            vosk_model_path=os.getenv("VOSK_MODEL_PATH", "vosk-model-small-ru-0.22"),
            conversation_timeout=int(os.getenv("CONVERSATION_TIMEOUT", "30")),
            tick_vibro=_bool("TICK_VIBRO"),
            listen_beep_freq=float(os.getenv("LISTEN_BEEP_FREQ", "200")),
            listen_beep_duration=float(os.getenv("LISTEN_BEEP_DURATION", "0.2")),
            listen_beep_volume=float(os.getenv("LISTEN_BEEP_VOLUME", "0.4")),
            tick_freq=float(os.getenv("TICK_FREQ", "350")),
            tick_duration=float(os.getenv("TICK_DURATION", "0.03")),
            tick_volume=float(os.getenv("TICK_VOLUME", "0.15")),
            tick_interval=float(os.getenv("TICK_INTERVAL", "2.0")),
            system_prompt_path=os.getenv("SYSTEM_PROMPT_PATH", default_prompt),
        )

    def load_system_prompt(self) -> str:
        """Read the system prompt from the configured file."""
        path = Path(self.system_prompt_path)
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
        # Fallback if file is missing
        return (
            "You are Jarvis (Джарвис), a voice AI assistant. "
            "Respond concisely and conversationally. "
            'End with "[END]" when the conversation is finished.'
        )


# Module-level singleton — import this in all other modules
settings = Settings.from_env()
