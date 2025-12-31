from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
import onnxruntime as ort
from concurrent.futures import ThreadPoolExecutor
import io
import asyncio
import soundfile as sf
import time
from app.core.config import settings
from app.api.schemas import OpenAIInput, ModelList
from app.services.tts import tts_service
from app.utils.text import split_text_into_chunks, clean_text
from app.core.logging import logger
from app.core.database import verify_api_key, track_usage
from app.api.auth.models import ApiKey
from app.services.audio import AudioService, AudioNormalizer
from app.services.streaming_audio_writer import StreamingAudioWriter
from app.inference.base import AudioChunk

router = APIRouter()
executor = ThreadPoolExecutor(max_workers=settings.MAX_WORKERS)
concurrency_limiter = asyncio.Semaphore(settings.MAX_WORKERS * 50)
@router.post("/v1/audio/speech", responses={
    200: {
        "content": {"audio/mpeg": {}, "audio/wav": {}, "audio/flac": {}, "audio/ogg": {}, "audio/pcm": {}},
        "description": "The generated audio file.",
    }
})
async def generate_speech(
    data: OpenAIInput, 
    background_tasks: BackgroundTasks,
    api_key: ApiKey = Depends(verify_api_key)
):
    # 1. Calculate Cost
    char_count = len(data.input)
    cost = (char_count / 1_000_000) * api_key.price_per_million_chars
    
    # 2. Add Usage Tracking to Background Tasks
    background_tasks.add_task(track_usage, api_key, char_count, cost)
    logger.info(f"Queued billing for {api_key.name}: {char_count} chars, ${cost:.6f}")

    async with concurrency_limiter:
        if not tts_service.model:
            raise HTTPException(status_code=503, detail="Model loading")

        # Normalize text
        normalized_text = clean_text(data.input) if data.normalize else data.input
        logger.debug(f"Normalized text: {normalized_text[:100]}...")

        sample_rate = getattr(tts_service.model, 'sample_rate', settings.SAMPLE_RATE)
        
        media_types = {
            "mp3": "audio/mpeg", "wav": "audio/wav", "flac": "audio/flac",
            "opus": "audio/ogg", "pcm": "audio/pcm"
        }
        media_type = media_types.get(data.response_format, "audio/wav")
        filename = f"speech.{data.response_format}"

        start_time = time.time()

        if data.stream:
            headers = {
                "Content-Disposition": f'inline; filename="{filename}"',
                "X-Accel-Buffering": "no"
            }
            
            async def gen():
                writer = StreamingAudioWriter(format=data.response_format, sample_rate=sample_rate)
                first_byte_time = None
                try:
                    async for chunk in tts_service.generate_audio_stream(
                        normalized_text, data.voice, writer, speed=data.speed, 
                        output_format=data.response_format
                    ):
                        if chunk.output:
                            if first_byte_time is None:
                                first_byte_time = time.time()
                                ttfb = (first_byte_time - start_time) * 1000
                                logger.info(f"TTS Streaming TTFB: {ttfb:.2f}ms")
                            yield chunk.output
                finally:
                    writer.close()
                    total_time = (time.time() - start_time) * 1000
                    logger.info(f"TTS Streaming Total Time: {total_time:.2f}ms for {char_count} chars")

            return StreamingResponse(gen(), media_type=media_type, headers=headers)

        # Non-stream
        try:
            writer = StreamingAudioWriter(format=data.response_format, sample_rate=sample_rate)
            processed = await tts_service.generate_audio(
                normalized_text, data.voice, writer, speed=data.speed, 
                output_format=data.response_format
            )
            
            total_time = (time.time() - start_time) * 1000
            logger.info(f"TTS Non-Stream Total Time: {total_time:.2f}ms for {char_count} chars")
            
            if not processed.output:
                raise ValueError("No audio output generated")

            return StreamingResponse(
                io.BytesIO(processed.output), 
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
