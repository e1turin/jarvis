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
    # ── Identity ──────────────────────────────────────────
    agent_name: str = "Jarvis"
    wake_word_display: str = "Джарвис"

    # ── Wake word detection (Vosk) ────────────────────────
    wake_mode: bool = True
    wake_words: list[str] = field(default_factory=lambda: ["джарвис"])
    vosk_model_path: str = "vosk-model-small-ru-0.22"
    pre_wake_buffer_seconds: float = 3.0

    # ── LLM (OpenAI-compatible API) ───────────────────────
    llm_provider: str = "lmstudio"
    llm_base_url: str = "localhost:1234/v1"
    llm_api_key: str = ""
    llm_model: str = "google/gemma-4-12b-qat"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 1024
    llm_timeout: int = 30
    llm_max_retries: int = 1

    # ── Audio / Microphone ────────────────────────────────
    audio_sample_rate: int = 16000

    # ── Speech-to-Text (faster-whisper) ───────────────────
    stt_model: str = "base"

    # ── Voice Activity Detection ──────────────────────────
    vad_mode: bool = True
    vad_silence_timeout: float = 1.5
    vad_threshold: float = 0.02
    vad_block_size_ms: int = 50
    listener_max_wait: int = 10

    # ── Text-to-Speech ────────────────────────────────────
    tts_backend: str = "edge"
    tts_voice: str = "ru-RU-SvetlanaNeural"
    tts_rate: str = "+0%"
    tts_gen_timeout: int = 60

    # ── Conversation ──────────────────────────────────────
    conversation_timeout: int = 30
    sleep_words: str = "пока,до свидания,всё,свободен,bye,goodbye,спать,иди спать,отдыхай,закончили,хватит"

    # ── Sound feedback (beep / ticks) ─────────────────────
    tick_vibro: bool = False
    listen_beep_freq: float = 200
    listen_beep_duration: float = 0.2
    listen_beep_volume: float = 0.4
    tick_freq: float = 350
    tick_duration: float = 0.03
    tick_volume: float = 0.15
    tick_interval: float = 2.0
    sounds_sample_rate: int = 22050

    # ── System prompt ─────────────────────────────────────
    system_prompt_path: str = ""

    # ── Yandex TTS (advanced) ─────────────────────────────
    yc_api_key: str = ""
    yc_folder_id: str = ""
    tts_lang: str = "ru-RU"

    @classmethod
    def from_env(cls) -> "Settings":
        def _bool(key: str, default: str = "false") -> bool:
            return os.getenv(key, default).lower() in ("true", "1", "yes")

        wake_words_raw = os.getenv("WAKE_WORDS", "джарвис")
        wake_words = [w.strip().lower() for w in wake_words_raw.split(",")]

        # Default prompt path: next to this file
        default_prompt = str(Path(__file__).parent / "prompt.txt")

        return cls(
            # ── Identity ──
            agent_name=os.getenv("AGENT_NAME", "Jarvis"),
            wake_word_display=os.getenv("WAKE_WORD_DISPLAY", "")
                          or (wake_words[0].capitalize() if wake_words else "Джарвис"),

            # ── Wake word ──
            wake_mode=_bool("WAKE_MODE", "true"),
            wake_words=wake_words,
            vosk_model_path=os.getenv("VOSK_MODEL_PATH", "vosk-model-small-ru-0.22"),
            pre_wake_buffer_seconds=float(os.getenv("PRE_WAKE_BUFFER_SECONDS", "3.0")),

            # ── LLM ──
            llm_provider=os.getenv("LLM_PROVIDER", "undefined"),
            llm_base_url=os.getenv("LLM_BASE_URL", ""),
            llm_api_key=os.getenv("LLM_API_KEY", ""),
            llm_model=os.getenv("LLM_MODEL", "undefined"),
            llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            llm_max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1024")),
            llm_timeout=int(os.getenv("LLM_TIMEOUT", "30")),
            llm_max_retries=int(os.getenv("LLM_MAX_RETRIES", "1")),

            # ── Audio / Microphone ──
            audio_sample_rate=int(os.getenv("AUDIO_SAMPLE_RATE", "16000")),

            # ── STT ──
            stt_model=os.getenv("STT_MODEL", "base"),

            # ── VAD ──
            vad_mode=_bool("VAD_MODE", "true"),
            vad_silence_timeout=float(os.getenv("VAD_SILENCE_TIMEOUT", "1.5")),
            vad_threshold=float(os.getenv("VAD_THRESHOLD", "0.02")),
            vad_block_size_ms=int(os.getenv("VAD_BLOCK_SIZE_MS", "50")),
            listener_max_wait=int(os.getenv("LISTENER_MAX_WAIT", "10")),

            # ── TTS ──
            tts_backend=os.getenv("TTS_BACKEND", "edge").lower(),
            tts_voice=os.getenv("TTS_VOICE", "ru-RU-SvetlanaNeural"),
            tts_rate=os.getenv("TTS_RATE", "+0%"),
            tts_gen_timeout=int(os.getenv("TTS_GEN_TIMEOUT", "60")),

            # ── Conversation ──
            conversation_timeout=int(os.getenv("CONVERSATION_TIMEOUT", "30")),
            sleep_words=os.getenv("SLEEP_WORDS",
                "пока,до свидания,всё,свободен,bye,goodbye,спать,иди спать,отдыхай,закончили,хватит"),

            # ── Sound feedback ──
            tick_vibro=_bool("TICK_VIBRO"),
            listen_beep_freq=float(os.getenv("LISTEN_BEEP_FREQ", "200")),
            listen_beep_duration=float(os.getenv("LISTEN_BEEP_DURATION", "0.2")),
            listen_beep_volume=float(os.getenv("LISTEN_BEEP_VOLUME", "0.4")),
            tick_freq=float(os.getenv("TICK_FREQ", "350")),
            tick_duration=float(os.getenv("TICK_DURATION", "0.03")),
            tick_volume=float(os.getenv("TICK_VOLUME", "0.15")),
            tick_interval=float(os.getenv("TICK_INTERVAL", "2.0")),
            sounds_sample_rate=int(os.getenv("SOUNDS_SAMPLE_RATE", "22050")),

            # ── System prompt ──
            system_prompt_path=os.getenv("SYSTEM_PROMPT_PATH", default_prompt),

            # ── Yandex TTS ──
            yc_api_key=os.getenv("YC_API_KEY", ""),
            yc_folder_id=os.getenv("YC_FOLDER_ID", ""),
            tts_lang=os.getenv("TTS_LANG", "ru-RU"),
        )

    def load_system_prompt(self) -> str:
        """Read the system prompt from the configured file.
        Substitutes __AGENT_NAME__ and __WAKE_WORD__ with configured values.
        """
        path = Path(self.system_prompt_path)
        if path.exists():
            prompt = path.read_text(encoding="utf-8").strip()
        else:
            # Fallback if file is missing
            prompt = (
                f"You are {self.agent_name} ({self.wake_word_display}), "
                "a voice AI assistant. "
                "Respond concisely and conversationally. "
                'End with "[END]" when the conversation is finished.'
            )
        prompt = prompt.replace("__AGENT_NAME__", self.agent_name)
        prompt = prompt.replace("__WAKE_WORD__", self.wake_word_display)
        return prompt


# Module-level singleton — import this in all other modules
settings = Settings.from_env()
