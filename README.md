# Production Ready Supertonic FastAPI

This is a production-ready, OpenAI-compatible text-to-speech API using [Supertonic](https://github.com/supertone-inc/supertonic-py).

## Features
- **OpenAI Compatibility**: Drop-in replacement for input/output of OpenAI TTS API.
- **Auto-Chunking**: Handles long text input automatically.
- **Voices**: Supports all Supertonic voices (F1-F5, M1-M5) mapped to OpenAI names (alloy, echo, etc.).
- **Streaming**: Supports chunked transfer encoding (playing while generating).
- **Hardward Acceleration**: Support for NVIDIA GPU (CUDA) and Mac Apple Silicon (CoreML) via ONNX Runtime.
- **Dockerized**: Ready for deployment.

## Quick Start (Local)

1. **Setup**:
   ```bash
   ./scripts/setup.sh
   ```

2. **Run**:
   ```bash
   ./scripts/start.sh
   # Server listens on http://0.0.0.0:8800
   ```

## Production Deployment (Docker)

The easiest way to run in production is using Docker Compose, which includes an Nginx load balancer.

### Using Docker Compose
1. **Start**:
   ```bash
   docker compose up -d
   ```

2. **Scale**:
   ```bash
   # Scale to 3 worker instances
   docker compose up -d --scale api=3
   ```

### Individual Image
1. **Build**:
   ```bash
   docker build -t supertonic-tts .
   ```

2. **Run**:
   ```bash
   # CPU / Mac (Recommended for Docker on Mac)
   docker run -p 8800:8800 supertonic-tts

   # NVIDIA GPU (Requires nvidia-container-toolkit)
   docker run --gpus all -p 8800:8800 supertonic-tts
   ```

## Configuration (.env)

| Variable | Default | Description |
|---|---|---|
| `PORT` | 8800 | Port to listen on |
| `FORCE_PROVIDERS` | auto | Force specific ORT provider: `cuda`, `coreml`, `cpu`, or `auto` |
| `MODEL_THREADS` | 0 | Intra-op threads (0=auto) |
| `MAX_WORKERS` | 4 | Thread pool workers for concurrent requests |

## API Usage

**POST** `/v1/audio/speech`

```json
{
  "model": "tts-1",
  "input": "Hello, this is a test.",
  "voice": "alloy",
  "stream": true
}
```

**Get Voices**: `/voices`
**Health Check**: `/health`
