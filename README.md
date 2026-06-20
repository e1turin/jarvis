# 🎙️ Jarvis — Voice AI Assistant

A fully offline voice AI assistant for macOS (works on Linux too).  
Speak to it, it talks back. Wake word ("Джарвис"), STT, LLM, TTS — all local.

## Features

- **Wake word activation** — Say "Джарвис" to wake the assistant (offline, Vosk)
- **Voice Activity Detection (VAD)** — Automatically starts/stops recording based on silence
- **Speech-to-Text** — Local transcription via faster-whisper
- **LLM reasoning** — Any OpenAI-compatible API (LM Studio or Ollama)
- **Text-to-Speech** — Multiple backends: macOS `say` (offline, built-in), `edge-tts` (online, best quality), `espeak-ng` (offline, cross-platform)
- **Continuous barge-in** — Say the wake word at any time to interrupt — during LLM thinking, TTS generation, or playback
- **Conversation history integrity** — Interrupted turns leave no trace in history. The LLM always sees a clean, sequential conversation
- **Rolling pre-wake buffer** — Speech right before the wake word is preserved, not lost
- **Built-in web search** — Ask "what's the weather?" or "search for..." and Jarvis searches DuckDuckGo (free, no API key, no setup)
- **Conversation control** — LLM decides when the conversation is done (via `[END]` marker)
- **Sleep timeout** — Returns to wake-word listening after inactivity

## Demo

```
--- Jarvis Voice AI Assistant ---
Initializing modules...
🔊 Vosk model loaded | Wake words: джарвис
System ready. Provider: lmstudio | Model: google/gemma-4-12b-qat
Say 'Jarvis' or 'Джарвис' to wake me up.
💤 Waiting... (say: Джарвис)

🔊 Wake word detected!
🎙️ Conversation started. Say 'Джарвис' to interrupt me.

🎤 Listening (VAD, silence timeout: 1.5s)...
   🔴 Listening...
   ✅ Done
📝 Transcribing...
You: привет
🧠 Thinking...
Jarvis: Здравствуйте! Чем я могу вам помочь?
🎤 Listening (VAD, silence timeout: 1.5s)...
```

## Prerequisites

- **Python 3.10+** (managed with [uv](https://docs.astral.sh/uv/))
- **LM Studio** or **Ollama** (or any OpenAI-compatible API) — for LLM
- **Internet connection** — only needed for `edge-tts` or first-time model downloads

## Setup

### 1. Install dependencies

```bash
cd jarvis
uv sync
```

This installs all Python packages from `pyproject.toml`.

### 2. Download Vosk model

The wake word detector uses a Russian Vosk model. Download it:

```bash
# Option A: curl
curl -L -o vosk-model-small-ru-0.22.zip \
  https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip
unzip vosk-model-small-ru-0.22.zip
rm vosk-model-small-ru-0.22.zip

# Option B: wget
wget https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip
unzip vosk-model-small-ru-0.22.zip
rm vosk-model-small-ru-0.22.zip
```

The model directory (`vosk-model-small-ru-0.22/`) should be in the project root.

> Other Vosk models: https://alphacephei.com/vosk/models

### 3. Configure environment

Copy the template and edit:

```bash
cp .env.example .env
```

Then edit `.env` with your settings. See **Quick Start** below for typical configs.

### 4. Choose your TTS backend

Jarvis supports several TTS backends. For **fully offline operation**, use macOS `say`:

| Backend | Online | Quality | Platform |
|---------|--------|---------|----------|
| `say`   | ❌ Offline | ★★★ Good | macOS only (built-in) |
| `edge`  | ⚠️ Internet | ★★★★ Best | Cross-platform |
| `espeak`| ❌ Offline | ★★ Robotic | Cross-platform (install espeak-ng) |
| `yandex`| ⚠️ Internet | ★★★★ Best | Requires Yandex Cloud API key |
| `print` | ❌ Offline | — | No audio, debug only |

**Fully offline config (macOS):**

```env
TTS_BACKEND=say
TTS_VOICE=Milena
```

The `say` command is built into macOS and works completely offline.
List available Russian voices: `say -v '?' | grep ru`

**Online (best quality):**

```env
TTS_BACKEND=edge
TTS_VOICE=ru-RU-SvetlanaNeural
```

**Cross-platform offline (robotic but works everywhere):**

```bash
# Install espeak-ng first:
#   brew install espeak-ng       (macOS)
#   apt install espeak-ng        (Linux)

# Then in .env:
TTS_BACKEND=espeak
TTS_VOICE=ru
```

### 5. Start the LLM server

**Option A — LM Studio:**
1. Open LM Studio, load your model (e.g. `google/gemma-4-12b-qat`)
2. Go to **Local Server** tab → click **Start Server** (default port: 1234)
3. Verify: `curl http://localhost:1234/v1/models`

**Option B — Ollama (Docker):**
```bash
docker run -d --name jarvis-ollama -p 11434:11434 -v ollama_data:/root/.ollama ollama/ollama
docker exec jarvis-ollama ollama pull gemma3:12b
# Set LLM_BASE_URL=http://localhost:11434/v1 in .env
```

### 6. Run Jarvis

```bash
uv run jarvis
```

## LLM Server Setup

Jarvis needs an OpenAI-compatible LLM server running.

**Option A — LM Studio (recommended for macOS):**
1. Open LM Studio, load your model (e.g. `google/gemma-4-12b-qat`)
2. Go to **Local Server** tab → click **Start Server** (default port: 1234)
3. Verify: `curl http://localhost:1234/v1/models`

**Option B — Ollama:**
```bash
# Install Ollama: https://ollama.com
docker run -d --name jarvis-ollama -p 11434:11434 -v ollama_data:/root/.ollama ollama/ollama
# or: brew install ollama && ollama serve

# Pull a model:
docker exec jarvis-ollama ollama pull gemma3:12b
# or: ollama pull gemma3:12b

# Update .env:
#    LLM_BASE_URL=http://localhost:11434/v1
#    LLM_API_KEY=ollama
#    LLM_MODEL=gemma3:12b
```

## Usage

| Action | Say |
|--------|-----|
| Wake up | "Джарвис" |
| Ask anything | Your question |
| Interrupt | "Джарвис" (at any time — even during TTS generation) |
| End conversation | "Пока", "до свидания", "спать", or let timeout expire |
| Exit | `Ctrl+C` |

The LLM will naturally end the conversation with `[END]` when it determines the discussion is finished.

## Configuration Reference

All settings live in `.env`. Copy the template (`cp .env.example .env`) and edit.
Settings are split into two groups:

| Group | Sections | Who needs it |
|-------|----------|-------------|
| **🟢 Simple** | 1–4 | Everyone — these are the core settings to get Jarvis running |
| **🟠 Advanced** | 5–13 | Only if you need to tweak wake word, VAD, STT, sound, proxy, etc. |

---

## 🟢 SIMPLE SETTINGS

### Section 1 — Identity
| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_NAME` | `Jarvis` | Agent name used in console (`--- Jarvis ---`, `Jarvis: text`) |
| `WAKE_WORD_DISPLAY` | `Джарвис` | Display name for wake word in UI. Falls back to first WAKE_WORDS entry (capitalized) |
| `WAKE_WORDS` | `джарвис` | Comma-separated wake words (lowercase) that trigger/interrupt |

### Section 2 — LLM (OpenAI-compatible API)
| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_BASE_URL` | `http://localhost:1234/v1` | API base URL (LM Studio, Ollama, OpenAI) |
| `LLM_API_KEY` | — | API key (not needed for LM Studio) |
| `LLM_MODEL` | `google/gemma-4-12b-qat` | Model name |
| `LLM_TEMPERATURE` | `0.7` | Response creativity (0.0–1.0) |
| `LLM_MAX_TOKENS` | `1024` | Max response length |
| `LLM_TIMEOUT` | `30` | HTTP client timeout (s) |
| `LLM_MAX_RETRIES` | `1` | Max API retries on failure |

### Section 3 — Text-to-Speech
| Variable | Default | Description |
|----------|---------|-------------|
| `TTS_BACKEND` | `edge` | Backend: `edge`, `say`, `espeak`, `yandex`, or `print` |
| `TTS_VOICE` | `ru-RU-SvetlanaNeural` | Voice name |
| `TTS_RATE` | `+0%` | Speech rate: `+0%` normal, `+20%` faster, `-20%` slower |
| `TTS_VOLUME` | `1.0` | Playback volume (0.0–1.0, macOS `afplay` only) |
| `TTS_GEN_TIMEOUT` | `60` | TTS generation timeout (s) |

### Section 4 — Conversation
| Variable | Default | Description |
|----------|---------|-------------|
| `CONVERSATION_TIMEOUT` | `30` | Inactivity timeout (s) before returning to sleep |
| `SLEEP_WORDS` | `пока,...` | Comma-separated words to end conversation |

---

## 🟠 ADVANCED SETTINGS

### Section 5 — Wake Word Detection (Vosk)
| Variable | Default | Description |
|----------|---------|-------------|
| `WAKE_MODE` | `true` | Enable wake word detection (false = always listening) |
| `VOSK_MODEL_PATH` | `vosk-model-small-ru-0.22` | Path to Vosk model directory |
| `PRE_WAKE_BUFFER_SECONDS` | `3.0` | Seconds of audio kept before wake word (rolling buffer) |

> Wake words themselves are set in **Section 1** (`WAKE_WORDS`). This section covers detection behaviour.

### Section 6 — Voice Activity Detection
| Variable | Default | Description |
|----------|---------|-------------|
| `VAD_MODE` | `true` | Enable VAD (false = record fixed duration) |
| `VAD_SILENCE_TIMEOUT` | `1.5` | Silence (s) before recording stops |
| `VAD_THRESHOLD` | `0.02` | Energy threshold (lower = more sensitive) |
| `VAD_BLOCK_SIZE_MS` | `50` | VAD analysis window (ms) |
| `LISTENER_MAX_WAIT` | `10` | Max seconds to wait for initial speech before giving up |

### Section 7 — Speech-to-Text (faster-whisper)
| Variable | Default | Description |
|----------|---------|-------------|
| `STT_MODEL` | `base` | Model size: `tiny`, `base`, `small`, `medium`, `large-v3` |
| `STT_DEVICE` | `cpu` | Device: `cpu` or `cuda` |
| `STT_COMPUTE_TYPE` | `int8` | Compute type: `int8`, `float16`, `float32` |

### Section 8 — Audio / Microphone
| Variable | Default | Description |
|----------|---------|-------------|
| `AUDIO_SAMPLE_RATE` | `16000` | Sample rate for mic capture (Hz) |

### Section 9 — Sound Feedback (beep / ticks)
| Variable | Default | Description |
|----------|---------|-------------|
| `TICK_VIBRO` | `false` | Use system beep for tick (may trigger haptic on Force Touch Macs) |
| `LISTEN_BEEP_FREQ` | `200` | Listening beep frequency (Hz) |
| `LISTEN_BEEP_DURATION` | `0.2` | Listening beep duration (s) |
| `LISTEN_BEEP_VOLUME` | `0.4` | Listening beep volume (0.0–1.0) |
| `TICK_FREQ` | `350` | Thinking tick frequency (Hz) |
| `TICK_DURATION` | `0.03` | Thinking tick duration (s) |
| `TICK_VOLUME` | `0.15` | Thinking tick volume (0.0–1.0) |
| `TICK_INTERVAL` | `2.0` | Interval between thinking ticks (s) |
| `SOUNDS_SAMPLE_RATE` | `22050` | Sample rate for beep/tick WAV generation |

### Section 10 — Proxy (HTTP / HTTPS / SOCKS5)
| Variable | Default | Description |
|----------|---------|-------------|
| `HTTP_PROXY` | — | HTTP proxy URL (`http://host:port`) |
| `HTTPS_PROXY` | — | HTTPS/SOCKS5 proxy URL (`socks5://host:1080`) |
| `NO_PROXY` | `localhost,127.0.0.1,::1` | Comma-separated hosts to bypass proxy |

### Section 11 — System Prompt
| Variable | Default | Description |
|----------|---------|-------------|
| `SYSTEM_PROMPT_PATH` | `src/jarvis/prompt.txt` | Path to system prompt text file |

### Section 12 — Yandex TTS
| Variable | Default | Description |
|----------|---------|-------------|
| `YC_API_KEY` | — | Yandex Cloud API key for SpeechKit |
| `YC_FOLDER_ID` | — | Yandex Cloud folder ID |
| `TTS_LANG` | `ru-RU` | TTS language code |

### Section 13 — Temporary Files
| Variable | Default | Description |
|----------|---------|-------------|
| `TEMP_DIR` | `.` | Directory for temporary audio files |

### TTS Voices

**Edge TTS** (internet required):
- `ru-RU-SvetlanaNeural` (female)
- `ru-RU-DariyaNeural` (female)
- `ru-RU-DmitryNeural` (male)

List all: `uv run python -m edge_tts --list-voices | grep ru`

**macOS `say`** (offline, built-in):
- `Milena` (female, Russian)

List installed: `say -v '?' | grep ru`

**espeak-ng** (offline, cross-platform, robotic):
- `ru` (Russian)

List all: `espeak-ng --voices | grep ru`

**Yandex SpeechKit** — if `TTS_BACKEND=yandex`, set `YC_API_KEY`, `YC_FOLDER_ID`, `TTS_VOICE=alisa` (or `filipp`, etc.).

### Wake Word Recording Tool

Test the wake word detector with your voice:

```bash
uv run python tools/record_wake.py
```

This records a 3-second sample, saves it to `recordings/`, and tests if Vosk detects the wake word. Useful for tuning `VAD_THRESHOLD` or checking microphone placement.

## Project Structure

```
jarvis/
├── .env.example               # Configuration template (copy to .env)
├── .gitignore
├── .python-version            # Python version for uv
├── README.md
├── pyproject.toml             # Dependencies & build config
├── vosk-model-small-ru-0.22/  # Vosk model (downloaded separately)
├── tools/
│   └── record_wake.py         # Wake word testing utility
└── src/
    └── jarvis/
        ├── __init__.py
        ├── config.py          # Centralized config (typed, from .env)
        ├── main.py            # Orchestrator — wake → converse → sleep
        ├── brain.py           # Conversation manager (LLM + tools + history)
        ├── llm.py             # Pure LLM client (OpenAI wrapper, no tools/history)
        ├── tools.py           # Built-in tool defs + implementations (web_search)
        ├── listener.py        # Facade: recorder + STT + pre-wake buffer
        ├── recorder.py        # Audio capture (VAD + fixed duration)
        ├── stt.py             # Speech-to-text (faster-whisper)
        ├── speaker.py         # Facade: TTS + cancellable playback
        ├── tts.py             # TTS generation backends (edge, say, espeak, yandex)
        ├── player.py          # Audio playback (cancellable, afplay/ffplay/aplay)
        ├── wake.py            # Vosk wake word + barge-in detection
        ├── sounds.py          # Audio feedback cues (beep, ticks)
        └── prompt.txt         # System prompt (editable text file)
```

### Architecture

```mermaid
flowchart TD
    A[💤 Waiting for wake word] -->|"say Джарвис"| B[🎙️ Conversation]
    B --> C[🎤 Listen with VAD]
    C --> D[📝 Transcribe with Whisper]
    D --> E[🧠 LLM reasoning with tools]
    E -->|tool_call| F[🔧 web_search]
    F --> E
    E -->|text| G{"Has [END]?"}
    G -->|No| H[🔊 Generate TTS + Play]
    H -.->|"say Джарвис"| I[⏹️ Barge-in interrupt]
    I -->|mic monitor| C
    H -->|"playback ends"| C
    H -->|silence timeout| A
    G -->|Yes| J[🔊 Speak final response]
    J --> A
```

### Dependencies

Defined in `pyproject.toml`. Install all: `uv sync`

- `openai` — LLM API client
- `python-dotenv` — environment variables
- `pydantic` — data models
- `sounddevice`, `numpy`, `scipy` — audio capture & processing
- `faster-whisper` — local speech-to-text (CTranslate2-based, fast)
- `edge-tts` — Microsoft Edge TTS voice synthesis
- `vosk` — offline speech recognition for wake word
- `httpx[socks]` — HTTP client (proxy support, SOCKS5, Yandex TTS)
- `ddgs` — web search via DuckDuckGo (built-in, no API key needed)

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Connection refused` on LLM | LM Studio server not running. Start it. |
| Wake word not detected | Speak clearly. Try lowering `VAD_THRESHOLD` in `.env`. |
| Always detecting wake word | Raise `VAD_THRESHOLD`. Check for background noise. |
| TTS error (edge) | `edge-tts` needs internet. Check connection or switch to `say` backend. |
| TTS error (say) | `TTS_BACKEND=say` requires macOS. Voice must be installed in System Settings → Accessibility → Spoken Content. |
| TTS error (espeak) | Install espeak-ng: `brew install espeak-ng` (macOS) / `apt install espeak-ng` (Linux). |
| Barge-in not working | Check `WAKE_MODE=true` and that the response text doesn't contain the wake word (echo protection). |
| Microphone not working | Check macOS permissions: System Settings → Privacy → Microphone |
| Vosk model not found | Ensure `VOSK_MODEL_PATH` points to the unzipped model directory. |
| LLM behaves poorly | Small models (<7B) struggle with conversation control. Use gemma-4-12b or larger. |
| `thought_signature` error (Gemini) | The code automatically falls back to no-tools mode for Gemini models. Web search will be unavailable for that turn. |
| Web search returns 0 results | DuckDuckGo may be blocked in your region. Try setting `HTTPS_PROXY` in `.env`. |

## Tips

- **Wake word tuning**: Use `tools/record_wake.py` to test how well Vosk hears you. Adjust `VAD_THRESHOLD` and mic position.
- **LLM structured output**: If you enable JSON mode in LM Studio UI, the code gracefully degrades (it uses `[END]` marker instead).
- **No audio mode**: Set `TTS_BACKEND=print` and `TTS_VOICE=` to debug without sound.
- **Small LLMs**: Qwen3.5-0.8B is too small for reliable conversation control. For small models, use `WAKE_MODE=false` (always listening) and keep responses very short.

## License

MIT
