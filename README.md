# 🎙️ Supertonic TTS API

<div align="center">

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker)](Dockerfile)

**OpenAI-compatible Text-to-Speech API**

[Features](#-features) • [Quick Start](#-quick-start) • [API Reference](#-api-reference) • [Deployment](#-deployment) • [Configuration](#-configuration)

</div>

---

## ✨ Features

- 🚀 **OpenAI-Compatible API** - Drop-in replacement for OpenAI's TTS API
- ⚡ **High Performance** - Optimized with NumPy vectorization and async processing
- 🎵 **Multiple Formats** - Support for MP3, WAV, FLAC, Opus, AAC, and PCM
- 🗣️ **Multiple Voices** - OpenAI voice names mapped to native Supertonic styles
- 🔐 **API Key Authentication** - Secure access with usage tracking
- 🐳 **Docker Ready** - Production-ready containerization with nginx
- 📊 **GPU Acceleration** - Support for CUDA, CoreML, and Metal backends
- 🔊 **Smart Text Processing** - Automatic text normalization and chunking
- 🌐 **Multi-Version Support** - Supports both Supertonic v1 and v2 models

## 📋 Requirements

- Python 3.10+
- ONNX Runtime (CPU/CUDA/CoreML)
- Supertonic TTS library

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/supertonic-fastapi.git
cd supertonic-fastapi

# Start with Docker Compose
docker-compose up -d

# API will be available at http://localhost:8800
```

### Manual Installation

```bash
# Clone and install
git clone https://github.com/yourusername/supertonic-fastapi.git
cd supertonic-fastapi

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m app.main
```

### Quick Test

```bash
# Generate speech
curl -X POST "http://localhost:8800/v1/audio/speech" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Hello, this is a test of the Supertonic TTS API!",
    "voice": "alloy",
    "response_format": "mp3"
  }' \
  --output speech.mp3
```

## 📖 API Reference

### Generate Speech

**POST** `/v1/audio/speech`

```bash
curl -X POST "http://localhost:8800/v1/audio/speech" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "Your text here...",
    "voice": "alloy",
    "response_format": "mp3",
    "speed": 1.0
  }' \
  --output output.mp3
```

#### Parameters

| Parameter         | Type    | Default    | Description                                                             |
| ----------------- | ------- | ---------- | ----------------------------------------------------------------------- |
| `model`           | string  | `tts-1`    | TTS model (tts-1, tts-1-hd, tts-2, tts-2-hd, supertonic, supertonic-v2) |
| `input`           | string  | _required_ | Text to convert (max 4096 chars)                                        |
| `voice`           | string  | `alloy`    | Voice: alloy, echo, fable, onyx, nova, shimmer                          |
| `response_format` | string  | `mp3`      | Output format: mp3, opus, aac, flac, wav, pcm                           |
| `speed`           | float   | `1.0`      | Speed multiplier (0.25 to 4.0)                                          |
| `normalize`       | boolean | `true`     | Pre-normalize text for better synthesis                                 |

### List Models

**GET** `/v1/models`

```bash
curl "http://localhost:8800/v1/models"
```

### List Voices

**GET** `/voices`

```bash
curl "http://localhost:8800/voices" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Health Check

**GET** `/health`

```bash
curl "http://localhost:8800/health"
```

## 🎭 Available Voices

| OpenAI Voice | Description                    |
| ------------ | ------------------------------ |
| `alloy`      | Neutral, balanced voice        |
| `echo`       | Warm, conversational voice     |
| `fable`      | Expressive, storytelling voice |
| `onyx`       | Deep, authoritative voice      |
| `nova`       | Friendly, upbeat voice         |
| `shimmer`    | Soft, gentle voice             |

## ⚙️ Configuration

Environment variables can be set in `.env` file:

```env
# Server
HOST=0.0.0.0
PORT=8800
LOG_LEVEL=INFO

# Model Performance
MODEL_THREADS=12
MODEL_INTER_THREADS=12
MAX_WORKERS=8

# GPU Acceleration
FORCE_PROVIDERS=auto  # auto, cuda, coreml, metal, cpu

# Audio Settings
SAMPLE_RATE=44100
gap_trim_ms=100

# Model Version (v1 or v2)
DEFAULT_MODEL_VERSION=v1
```

### GPU Acceleration

Set `FORCE_PROVIDERS` based on your hardware:

| Value    | Description                         |
| -------- | ----------------------------------- |
| `auto`   | Auto-detect best available provider |
| `cuda`   | NVIDIA GPU acceleration             |
| `coreml` | Apple CoreML (M-series chips)       |
| `metal`  | Apple Metal (maps to CoreML)        |
| `cpu`    | CPU only                            |

## 🐳 Deployment

### Docker Compose (Production)

```yaml
# docker-compose.yml
version: "3.8"
services:
  tts-api:
    build: .
    ports:
      - "8800:8800"
    environment:
      - FORCE_PROVIDERS=auto
    volumes:
      - ./data:/app/data
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: supertonic-tts
spec:
  replicas: 2
  selector:
    matchLabels:
      app: supertonic-tts
  template:
    metadata:
      labels:
        app: supertonic-tts
    spec:
      containers:
        - name: tts-api
          image: supertonic-tts:latest
          ports:
            - containerPort: 8800
          resources:
            limits:
              nvidia.com/gpu: 1 # Optional GPU
```

## 📊 Performance

Optimized for high-throughput production workloads:

- **NumPy Vectorization** - Audio processing uses vectorized operations for 10x faster silence detection
- **Pre-compiled Regex** - Text normalization patterns compiled at startup
- **Async Processing** - Non-blocking I/O for concurrent requests
- **Connection Pooling** - Efficient database connections with Tortoise ORM
- **Semaphore Limits** - Configurable concurrency control

## 🔧 Development

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run in development mode
uvicorn app.main:app --reload --port 8800

# Run tests
python -m pytest tests/
```

## 📁 Project Structure

```
supertonic-fastapi/
├── app/
│   ├── api/
│   │   ├── routes.py          # API endpoints
│   │   ├── schemas.py         # Pydantic models
│   │   ├── deps.py            # Dependencies
│   │   └── auth/              # Authentication
│   ├── core/
│   │   ├── config.py          # Configuration
│   │   ├── database.py        # Database setup
│   │   └── voices.py          # Voice mappings
│   ├── services/
│   │   ├── tts.py             # TTS service
│   │   ├── audio.py           # Audio processing
│   │   └── streaming_audio_writer.py  # Format encoding
│   ├── utils/
│   │   └── text.py            # Text processing
│   ├── inference/
│   │   └── base.py            # Data models
│   └── main.py                # FastAPI app
├── tests/
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Supertonic](https://github.com/supertoneinc/supertonic) - TTS engine
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [PyAV](https://pyav.org/) - Audio encoding

---

<div align="center">

**[⬆ Back to Top](#️-supertonic-tts-api)**

Made with ❤️ by the community

</div>
