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
   ./setup.sh
   ```

2. **Run**:
   ```bash
   ./start.sh
   # Server listens on http://0.0.0.0:8800
   ```

## Production Deployment (Docker)

### GPU (NVIDIA)
Ensure you have the NVIDIA Container Toolkit installed.

1. **Build**:
   ```bash
   docker build -t supertonic-tts .
   ```

2. **Run**:
   ```bash
   docker run --gpus all -p 8800:8800 supertonic-tts
   ```

### Mac / CPU
1. **Build**:
   ```bash
   docker build -t supertonic-tts .
   ```

2. **Run**:
   ```bash
   docker run -p 8800:8800 supertonic-tts
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
