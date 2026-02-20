import time
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.core.config import settings
from app.core.voices import OPENAI_VOICE_NAMES
from app.api.schemas import OpenAIInput
from app.api.deps import get_api_key
from app.api.auth.models import ApiKey
from app.services.tts import tts_service
from app.utils.text import clean_text
from app.core.logging import logger
from app.core.database import track_usage
from app.services.streaming_audio_writer import StreamingAudioWriter

router = APIRouter()

# Concurrency limiter for TTS requests
concurrency_limiter = asyncio.Semaphore(settings.MAX_WORKERS * 50)

# Media type mappings
MEDIA_TYPES = {
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "flac": "audio/flac",
    "opus": "audio/ogg",
    "pcm": "audio/pcm",
}


@router.post("/v1/audio/speech")
async def generate_speech(
    data: OpenAIInput,
    api_key: ApiKey = Depends(get_api_key),
):
    """Generate speech from text using TTS."""
    try:
        # Calculate and track usage
        char_count = len(data.input)
        cost = (char_count / 1_000_000) * api_key.price_per_million_chars
        asyncio.create_task(track_usage(api_key, char_count, cost))
        logger.info(f"Queued billing for {api_key.name}: {char_count} chars, ${cost:.6f}")

        # Check model availability
        if not tts_service.model:
            raise HTTPException(status_code=503, detail="Model loading")

        # Normalize text if requested
        normalized_text = clean_text(data.input) if data.normalize else data.input
        logger.debug(f"Normalized text: {normalized_text[:100]}...")

        sample_rate = getattr(tts_service.model, "sample_rate", settings.SAMPLE_RATE)
        media_type = MEDIA_TYPES.get(data.response_format, "audio/wav")
        filename = f"speech.{data.response_format}"

        # Determine model version from model name
        model_version = None
        if data.model in ["tts-2", "tts-2-hd", "supertonic-v2"]:
            model_version = "v2"

        start_time = time.time()

        try:
            writer = StreamingAudioWriter(
                format=data.response_format, sample_rate=sample_rate
            )

            processed = await tts_service.generate_audio(
                normalized_text,
                data.voice,
                writer,
                speed=data.speed,
                output_format=data.response_format,
                model_version=model_version,
            )

            total_time = (time.time() - start_time) * 1000
            logger.info(f"TTS Total Time: {total_time:.2f}ms for {char_count} chars")

            if not processed.output:
                raise ValueError("No audio output generated")

            return Response(
                content=bytes(processed.output),
                media_type=media_type,
                headers={"Content-Disposition": f'inline; filename="{filename}"'},
            )

        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Unhandled error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/v1/models")
async def list_models():
    """List available TTS models."""
    import onnxruntime as ort
    return {
        "data": [
            {"id": "tts-1", "created": 1677610602, "owned_by": "openai"},
            {"id": "tts-1-hd", "created": 1677610602, "owned_by": "openai"},
            {"id": "tts-2", "created": 1704067200, "owned_by": "openai"},
            {"id": "tts-2-hd", "created": 1704067200, "owned_by": "openai"},
            {
                "id": "supertonic",
                "created": 1677610602,
                "owned_by": "supertone",
                "providers": ort.get_available_providers(),
            },
            {
                "id": "supertonic-v2",
                "created": 1704067200,
                "owned_by": "supertone",
                "version": "2.0",
                "providers": ort.get_available_providers(),
            },
        ]
    }


@router.get("/voices")
async def list_voices():
    """List available voices."""
    if not tts_service.model:
        raise HTTPException(status_code=503, detail="Model not ready")
    return {
        "voices": OPENAI_VOICE_NAMES,
        "native_styles": getattr(tts_service.model, "voice_style_names", []),
    }
