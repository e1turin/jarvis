# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for audio, Vosk, faster-whisper, and edge-tts
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    portaudio19-dev \
    alsa-utils \
    pulseaudio-utils \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
# uv.lock is optional — uv will resolve from pyproject.toml if absent
COPY pyproject.toml ./
COPY src/ ./src/
COPY tools/ ./tools/

# Install uv and Python dependencies
RUN pip install --no-cache-dir uv && \
    uv sync --no-dev

# Default: audio playback uses ffplay (Linux) or afplay (macOS - not in Docker)
# Set PULSE_SERVER if using PulseAudio passthrough
ENV PULSE_SERVER=unix:/run/user/1000/pulse/native
ENV TTS_BACKEND=edge
ENV STT_MODEL=base

# Vosk model is expected to be mounted or downloaded
# Whisper models are downloaded on first use

ENTRYPOINT ["uv", "run", "jarvis"]
