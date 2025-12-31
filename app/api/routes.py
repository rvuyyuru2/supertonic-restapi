from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse, JSONResponse
import onnxruntime as ort
from concurrent.futures import ThreadPoolExecutor
import io
import asyncio
import soundfile as sf
from app.core.config import settings
from app.api.schemas import OpenAIInput, ModelList
from app.services.tts import tts_service
from app.utils.text import split_text_into_chunks, clean_text
from app.core.logging import logger
from app.core.database import verify_api_key, track_usage
from app.api.auth.models import ApiKey

router = APIRouter()
# ThreadPool limits parallel execution on the CPU.
executor = ThreadPoolExecutor(max_workers=settings.MAX_WORKERS)
# Semaphore to provide backpressure and avoid queuing too many requests if system is overloaded
concurrency_limiter = asyncio.Semaphore(settings.MAX_WORKERS * 10)

async def stream_generator(text_input: str, style, speed: float, fmt: str, sample_rate: int):
    loop = asyncio.get_event_loop()
    chunks = split_text_into_chunks(text_input)
    
    for chunk in chunks:
        try:
            async with concurrency_limiter:
                wav, _ = await loop.run_in_executor(
                    executor,
                    tts_service.synthesize,
                    chunk, style, speed
                )
            
            if wav.ndim == 2 and wav.shape[0] == 1:
                wav = wav.squeeze()
                
            buffer = io.BytesIO()
            sf_format = "WAV"
            if fmt == "mp3": sf_format = "MP3"
            elif fmt == "flac": sf_format = "FLAC"
            elif fmt == "opus": sf_format = "OGG"
            
            if fmt == "pcm":
                yield wav.tobytes()
            else:
                try:
                    sf.write(buffer, wav, sample_rate, format=sf_format)
                except Exception as e:
                    logger.warning(f"Failed to write chunk format {sf_format}, fallback to WAV: {e}")
                    sf.write(buffer, wav, sample_rate, format="WAV")
                
                yield buffer.getvalue()
        except Exception as e:
            logger.error(f"Stream synthesis error on chunk: {e}")
            break

@router.post("/v1/audio/speech", responses={
    200: {
        "content": {"audio/mpeg": {}, "audio/wav": {}, "audio/flac": {}, "audio/ogg": {}, "audio/pcm": {}},
        "description": "The generated audio file.",
    }
})
async def generate_speech(data: OpenAIInput, api_key: ApiKey = Depends(verify_api_key)):
    # 1. Calculate Cost
    char_count = len(data.input)
    cost = (char_count / 1_000_000) * api_key.price_per_million_chars
    
    # 2. Track Usage (Async fire and forget or await)
    try:
        await track_usage(api_key, char_count, cost)
        logger.info(f"Billing {api_key.name}: {char_count} chars, ${cost:.6f}")
    except Exception:
        logger.exception(f"Failed to track usage for {api_key.name}")
        raise HTTPException(status_code=500, detail="Billing logic failed")

    if not tts_service.model:
        raise HTTPException(status_code=503, detail="Model loading")

    # Normalize text
    normalized_text = clean_text(data.input)
    logger.debug(f"Normalized text: {normalized_text[:100]}...")

    try:
        style = tts_service.get_style(data.voice)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    sample_rate = getattr(tts_service.model, 'sample_rate', 44100)
    
    media_types = {
        "mp3": "audio/mpeg", "wav": "audio/wav", "flac": "audio/flac",
        "opus": "audio/ogg", "pcm": "audio/pcm"
    }
    media_type = media_types.get(data.response_format, "audio/wav")
    filename = f"speech.{data.response_format}"

    if data.stream:
        headers = {
            "Content-Disposition": f'inline; filename="{filename}"',
            "X-Accel-Buffering": "no"
        }
        
        async def gen():
            async for chunk in stream_generator(normalized_text, style, data.speed, data.response_format, sample_rate):
                yield chunk

        return StreamingResponse(
            gen(),
            media_type=media_type,
            headers=headers
        )

    # Non-stream
    try:
        loop = asyncio.get_event_loop()
        async with concurrency_limiter:
            wav, _ = await loop.run_in_executor(
                executor,
                tts_service.synthesize,
                normalized_text, style, data.speed
            )
        
        if wav.ndim == 2 and wav.shape[0] == 1:
            wav = wav.squeeze()
            
        buffer = io.BytesIO()
        sf_format = "WAV"
        if data.response_format == "mp3": sf_format = "MP3"
        elif data.response_format == "flac": sf_format = "FLAC"
        elif data.response_format == "opus": sf_format = "OGG"
        
        if data.response_format == "pcm":
            buffer.write(wav.tobytes())
        else:
            try:
                sf.write(buffer, wav, sample_rate, format=sf_format)
            except Exception as e:
                logger.warning(f"Failed to write format {sf_format}, fallback to WAV. Error: {e}")
                sf.write(buffer, wav, sample_rate, format="WAV")
                media_type = "audio/wav"

        buffer.seek(0)
        return StreamingResponse(
            buffer, 
            media_type=media_type,
            headers={"Content-Disposition": f'inline; filename="{filename}"'}
        )
        
    except Exception as e:
        logger.error(f"Synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/v1/models", response_model=ModelList)
async def list_models():
    return {
        "data": [
            {"id": "tts-1", "created": 1677610602, "owned_by": "openai"},
            {"id": "supertonic", "created": 1677610602, "owned_by": "supertone", 
             "providers": ort.get_available_providers()}
        ]
    }

@router.get("/voices")
async def list_voices():
    if not tts_service.model:
        return JSONResponse(status_code=503, content={"error": "Model not ready"})
    return {"voices": getattr(tts_service.model, 'voice_style_names', [])}
