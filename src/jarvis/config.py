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
    # ╔══════════════════════════════════════════════════════════╗
    # ║  🟢  SIMPLE SETTINGS  —  most users only need these     ║
    # ╚══════════════════════════════════════════════════════════╝

    # ═══════════════════════════════════════════════════════════
    #  SECTION 1 — IDENTITY
    # ═══════════════════════════════════════════════════════════
    agent_name: str = "Jarvis"
    """Name used in console messages (`--- Jarvis ---`, `Jarvis: text`)"""
    wake_word_display: str = "Джарвис"
    """Display name for the wake word in UI messages"""
    wake_words: list[str] = field(default_factory=lambda: ["джарвис"])
    """Comma-separated wake words (lowercase) that trigger/interrupt"""

    # ═══════════════════════════════════════════════════════════
    #  SECTION 2 — LLM (OpenAI-compatible API)
    # ═══════════════════════════════════════════════════════════
    llm_base_url: str = "http://localhost:1234/v1"
    """API base URL (LM Studio default: http://localhost:1234/v1)"""
    llm_api_key: str = ""
    """API key (not needed for LM Studio)"""
    llm_model: str = "google/gemma-4-12b-qat"
    """Model name"""
    llm_temperature: float = 0.7
    """Response creativity (0.0–1.0)"""
    llm_max_tokens: int = 1024
    """Max tokens per response"""
    llm_timeout: int = 30
    """HTTP client timeout (seconds)"""
    llm_max_retries: int = 1
    """Max API retries on failure"""

    # ═══════════════════════════════════════════════════════════
    #  SECTION 3 — TEXT-TO-SPEECH
    # ═══════════════════════════════════════════════════════════
    tts_backend: str = "edge"
    """Backend: edge, say, espeak, yandex, or print"""
    tts_voice: str = "ru-RU-SvetlanaNeural"
    """Voice name"""
    tts_rate: str = "+0%"
    """Speech rate: +0% normal, +20% faster, -20% slower"""
    tts_volume: float = 1.0
    """Playback volume (0.0–1.0, macOS afplay only)"""
    tts_gen_timeout: int = 60
    """TTS generation timeout (seconds)"""

    # ═══════════════════════════════════════════════════════════
    #  SECTION 4 — CONVERSATION
    # ═══════════════════════════════════════════════════════════
    conversation_timeout: int = 30
    """Inactivity timeout (seconds) before returning to sleep"""
    sleep_words: str = "пока,до свидания,всё,свободен,bye,goodbye,спать,иди спать,отдыхай,закончили,хватит"
    """Comma-separated words/phrases to end the conversation"""

    # ╔══════════════════════════════════════════════════════════╗
    # ║  🟠  ADVANCED SETTINGS  —  only if you need to tweak     ║
    # ╚══════════════════════════════════════════════════════════╝

    # ═══════════════════════════════════════════════════════════
    #  SECTION 5 — WAKE WORD DETECTION  (Vosk)
    # ═══════════════════════════════════════════════════════════
    wake_mode: bool = True
    """Enable wake word detection (false = always listening)"""
    vosk_model_path: str = "vosk-model-small-ru-0.22"
    """Path to Vosk model directory"""
    pre_wake_buffer_seconds: float = 3.0
    """Seconds of rolling audio kept before wake word detection"""

    # ═══════════════════════════════════════════════════════════
    #  SECTION 6 — VOICE ACTIVITY DETECTION
    # ═══════════════════════════════════════════════════════════
    vad_mode: bool = True
    """Enable VAD (false = record fixed duration)"""
    vad_silence_timeout: float = 1.5
    """Seconds of silence before recording stops"""
    vad_threshold: float = 0.02
    """Energy threshold (lower = more sensitive)"""
    vad_block_size_ms: int = 50
    """VAD analysis window in milliseconds"""
    listener_max_wait: int = 10
    """Max seconds to wait for initial speech before VAD gives up"""

    # ═══════════════════════════════════════════════════════════
    #  SECTION 7 — SPEECH-TO-TEXT  (faster-whisper)
    # ═══════════════════════════════════════════════════════════
    stt_model: str = "base"
    """Model size: tiny, base, small, medium, large-v3"""
    stt_device: str = "cpu"
    """Device: cpu or cuda"""
    stt_compute_type: str = "int8"
    """Compute type: int8, float16, float32"""

    # ═══════════════════════════════════════════════════════════
    #  SECTION 8 — AUDIO / MICROPHONE
    # ═══════════════════════════════════════════════════════════
    audio_sample_rate: int = 16000
    """Sample rate for microphone capture (Hz)"""

    # ═══════════════════════════════════════════════════════════
    #  SECTION 9 — SOUND FEEDBACK  (beep / ticks)
    # ═══════════════════════════════════════════════════════════
    tick_vibro: bool = False
    """Use system beep instead of audio tick (may trigger haptic on Macs)"""
    listen_beep_freq: float = 200
    """Listening beep frequency (Hz)"""
    listen_beep_duration: float = 0.2
    """Listening beep duration (seconds)"""
    listen_beep_volume: float = 0.4
    """Listening beep volume (0.0–1.0)"""
    tick_freq: float = 350
    """Thinking tick frequency (Hz)"""
    tick_duration: float = 0.03
    """Thinking tick duration (seconds)"""
    tick_volume: float = 0.15
    """Thinking tick volume (0.0–1.0)"""
    tick_interval: float = 2.0
    """Interval between thinking ticks (seconds)"""
    sounds_sample_rate: int = 22050
    """Sample rate for beep/tick WAV generation (Hz)"""

    # ═══════════════════════════════════════════════════════════
    #  SECTION 10 — PROXY  (HTTP / HTTPS / SOCKS5)
    # ═══════════════════════════════════════════════════════════
    http_proxy: str = ""
    """HTTP proxy URL (e.g. http://host:port)"""
    https_proxy: str = ""
    """HTTPS or SOCKS5 proxy URL (e.g. socks5://host:1080)"""
    no_proxy: str = ""
    """Comma-separated hosts to bypass proxy (e.g. localhost,127.0.0.1)"""

    # ═══════════════════════════════════════════════════════════
    #  SECTION 11 — SYSTEM PROMPT
    # ═══════════════════════════════════════════════════════════
    system_prompt_path: str = ""
    """Path to system prompt text file (defaults to prompt.txt next to config.py)"""

    # ═══════════════════════════════════════════════════════════
    #  SECTION 13 — YANDEX TTS  (requires cloud API key)
    # ═══════════════════════════════════════════════════════════
    yc_api_key: str = ""
    """Yandex Cloud API key for SpeechKit"""
    yc_folder_id: str = ""
    """Yandex Cloud folder ID"""
    tts_lang: str = "ru-RU"
    """TTS language code"""

    # ═══════════════════════════════════════════════════════════
    #  SECTION 14 — TEMPORARY FILES  (overrides for testing)
    # ═══════════════════════════════════════════════════════════
    temp_dir: str = "."
    """Directory for temporary audio files"""

    @classmethod
    def from_env(cls) -> "Settings":
        def _bool(key: str, default: str = "false") -> bool:
            return os.getenv(key, default).lower() in ("true", "1", "yes")

        wake_words_raw = os.getenv("WAKE_WORDS", "джарвис")
        wake_words = [w.strip().lower() for w in wake_words_raw.split(",")]

        # Default prompt path: next to this file
        default_prompt = str(Path(__file__).parent / "prompt.txt")

        return cls(
            # ╔═ SIMPLE SETTINGS ═╗

            # ── 1. IDENTITY ──
            agent_name=os.getenv("AGENT_NAME", "Jarvis"),
            wake_word_display=os.getenv("WAKE_WORD_DISPLAY", "")
                          or (wake_words[0].capitalize() if wake_words else "Джарвис"),
            wake_words=wake_words,

            # ── 2. LLM ──
            llm_base_url=os.getenv("LLM_BASE_URL", "http://localhost:1234/v1"),
            llm_api_key=os.getenv("LLM_API_KEY", ""),
            llm_model=os.getenv("LLM_MODEL", "google/gemma-4-12b-qat"),
            llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            llm_max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1024")),
            llm_timeout=int(os.getenv("LLM_TIMEOUT", "30")),
            llm_max_retries=int(os.getenv("LLM_MAX_RETRIES", "1")),

            # ── 3. TTS ──
            tts_backend=os.getenv("TTS_BACKEND", "edge").lower(),
            tts_voice=os.getenv("TTS_VOICE", "ru-RU-SvetlanaNeural"),
            tts_rate=os.getenv("TTS_RATE", "+0%"),
            tts_volume=float(os.getenv("TTS_VOLUME", "1.0")),
            tts_gen_timeout=int(os.getenv("TTS_GEN_TIMEOUT", "60")),

            # ── 4. CONVERSATION ──
            conversation_timeout=int(os.getenv("CONVERSATION_TIMEOUT", "30")),
            sleep_words=os.getenv("SLEEP_WORDS",
                "пока,до свидания,всё,свободен,bye,goodbye,спать,иди спать,отдыхай,закончили,хватит"),

            # ╔═ ADVANCED SETTINGS ═╗

            # ── 5. WAKE WORD ──
            wake_mode=_bool("WAKE_MODE", "true"),
            vosk_model_path=os.getenv("VOSK_MODEL_PATH", "vosk-model-small-ru-0.22"),
            pre_wake_buffer_seconds=float(os.getenv("PRE_WAKE_BUFFER_SECONDS", "3.0")),

            # ── 6. VAD ──
            vad_mode=_bool("VAD_MODE", "true"),
            vad_silence_timeout=float(os.getenv("VAD_SILENCE_TIMEOUT", "1.5")),
            vad_threshold=float(os.getenv("VAD_THRESHOLD", "0.02")),
            vad_block_size_ms=int(os.getenv("VAD_BLOCK_SIZE_MS", "50")),
            listener_max_wait=int(os.getenv("LISTENER_MAX_WAIT", "10")),

            # ── 7. STT ──
            stt_model=os.getenv("STT_MODEL", "base"),
            stt_device=os.getenv("STT_DEVICE", "cpu"),
            stt_compute_type=os.getenv("STT_COMPUTE_TYPE", "int8"),

            # ── 8. AUDIO ──
            audio_sample_rate=int(os.getenv("AUDIO_SAMPLE_RATE", "16000")),

            # ── 9. SOUND FEEDBACK ──
            tick_vibro=_bool("TICK_VIBRO"),
            listen_beep_freq=float(os.getenv("LISTEN_BEEP_FREQ", "200")),
            listen_beep_duration=float(os.getenv("LISTEN_BEEP_DURATION", "0.2")),
            listen_beep_volume=float(os.getenv("LISTEN_BEEP_VOLUME", "0.4")),
            tick_freq=float(os.getenv("TICK_FREQ", "350")),
            tick_duration=float(os.getenv("TICK_DURATION", "0.03")),
            tick_volume=float(os.getenv("TICK_VOLUME", "0.15")),
            tick_interval=float(os.getenv("TICK_INTERVAL", "2.0")),
            sounds_sample_rate=int(os.getenv("SOUNDS_SAMPLE_RATE", "22050")),

            # ── 10. PROXY ──
            http_proxy=os.getenv("HTTP_PROXY", ""),
            https_proxy=os.getenv("HTTPS_PROXY", ""),
            no_proxy=os.getenv("NO_PROXY", ""),

            # ── 11. SYSTEM PROMPT ──
            system_prompt_path=os.getenv("SYSTEM_PROMPT_PATH", default_prompt),

            # ── 12. YANDEX TTS ──
            yc_api_key=os.getenv("YC_API_KEY", ""),
            yc_folder_id=os.getenv("YC_FOLDER_ID", ""),
            tts_lang=os.getenv("TTS_LANG", "ru-RU"),

            # ── 13. TEMP FILES ──
            temp_dir=os.getenv("TEMP_DIR", "."),
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
