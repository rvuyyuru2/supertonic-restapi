# Supertonic FastAPI - High Performance OpenAI-Compatible TTS API

Supertonic FastAPI is a **production-ready**, **lightning-fast**, and **OpenAI-compatible** text-to-speech (TTS) API powered by [Supertonic](https://github.com/supertone-inc/supertonic-py). It is designed for high-concurrency environments, providing a seamless drop-in replacement for OpenAI's speech synthesis services while offering superior performance and flexibility.

## Key Features & SEO Benefits
- **OpenAI API Compatibility**: Full support for OpenAI's TTS endpoints and data formats. Use existing SDKs without modification.
- **Advanced Auto-Chunking**: Automatically handles long text inputs, ensuring smooth and consistent audio generation for long-form content.
- **Multilingual & Multi-Voice**: Supports a wide range of professional voices (F1-F5, M1-M5) mapped to standard OpenAI voice names (alloy, echo, fable, onyx, nova, shimmer).
- **Real-Time Streaming**: Implements chunked transfer encoding, allowing users to play audio while it's still being generated (LLM-ready).
- **GPU & CPU Hardware Acceleration**: Optimized for **NVIDIA CUDA** (GPU) and **Apple Silicon CoreML** (Mac) using ONNX Runtime for near-instant inference.
- **Dockerized for Scale**: Ready for containerized deployment with Nginx load balancing and multi-process support.
- **Professional Speech Synthesis**: High-quality, natural-sounding AI voices suitable for podcasts, narrations, and assistants.

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
