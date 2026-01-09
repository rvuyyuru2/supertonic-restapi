from robyn import SubRouter, Request, Response, jsonify
from robyn.responses import StreamingResponse
import onnxruntime as ort
import asyncio
import time
import json
from app.core.config import settings
from app.api.schemas import OpenAIInput
from app.services.tts import tts_service
from app.utils.text import clean_text
from app.core.logging import logger
from app.core.database import verify_api_key, track_usage, AuthError
from app.services.streaming_audio_writer import StreamingAudioWriter

router = SubRouter(__name__, prefix="")

def error_response(status_code: int, detail: str):
    return Response(
        status_code=status_code,
        headers={"Content-Type": "application/json"},
        description=json.dumps({"detail": detail})
    )

concurrency_limiter = asyncio.Semaphore(settings.MAX_WORKERS * 50)

@router.post("/v1/audio/speech")
async def generate_speech(request: Request):
    try:
        api_key = await verify_api_key(request)
    
        try:
            body_content = request.body
            if not body_content:
                return error_response(400, "Empty request body")
            
            if isinstance(body_content, bytes):
                body_content = body_content.decode("utf-8")
                
            body = json.loads(body_content)
            data = OpenAIInput(**body)
        except Exception as e:
            return error_response(400, f"Invalid JSON body: {str(e)}")

        # 1. Calculate Cost
        char_count = len(data.input)
        cost = (char_count / 1_000_000) * api_key.price_per_million_chars
        
        # 2. Add Usage Tracking to Background Tasks (Fire and forget)
        asyncio.create_task(track_usage(api_key, char_count, cost))
        logger.info(f"Queued billing for {api_key.name}: {char_count} chars, ${cost:.6f}")

        if not tts_service.model:
            return error_response(503, "Model loading")

        # Normalize text using the simplified clean_text
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

        # Synthesis is always asynchronous through loop.run_in_executor in tts_service
        try:
            writer = StreamingAudioWriter(format=data.response_format, sample_rate=sample_rate)
            
            # Use generate_audio which gathers all chunks but processes them asynchronously
            processed = await tts_service.generate_audio(
                normalized_text, data.voice, writer, speed=data.speed, 
                output_format=data.response_format
            )
            
            total_time = (time.time() - start_time) * 1000
            if data.stream:
                logger.info(f"TTS Stream (Gathered) Total Time: {total_time:.2f}ms for {char_count} chars")
            else:
                logger.info(f"TTS Non-Stream Total Time: {total_time:.2f}ms for {char_count} chars")
            
            if not processed.output:
                raise ValueError("No audio output generated")

            # Robyn 0.x only reliably handles binary data as full bytes in Response objects.
            return Response(
                status_code=200, 
                headers={
                    "Content-Disposition": f'inline; filename="{filename}"', 
                    "Content-Type": media_type
                },
                description=bytes(processed.output)
            )
            
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            return error_response(500, str(e))

    except AuthError as e:
        return error_response(e.status_code, e.detail)
    except Exception as e:
        import traceback
        logger.error(f"Unhandled error: {e}")
        logger.error(traceback.format_exc())
        return error_response(500, "Internal Server Error")

@router.get("/v1/models")
async def list_models(request: Request):
    return jsonify({
        "data": [
            {"id": "tts-1", "created": 1677610602, "owned_by": "openai"},
            {"id": "supertonic", "created": 1677610602, "owned_by": "supertone", 
             "providers": ort.get_available_providers()}
        ]
    })

@router.get("/voices")
async def list_voices(request: Request):
    if not tts_service.model:
        return error_response(503, "Model not ready")
    return jsonify({"voices": getattr(tts_service.model, 'voice_style_names', [])})
