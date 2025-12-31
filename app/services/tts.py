import logging
import asyncio
import numpy as np
import onnxruntime as ort
from supertonic import TTS
from app.core.config import settings
from app.inference.base import AudioChunk
from app.services.audio import AudioService, AudioNormalizer
from app.services.streaming_audio_writer import StreamingAudioWriter
from app.utils.text import smart_split
from app.api.schemas import NormalizationOptions

logger = logging.getLogger("supertonic-api")

class TTSService:
    _chunk_semaphore = asyncio.Semaphore(settings.MAX_WORKERS)

    def __init__(self):
        self.model = None
        self._apply_patches()
        
    def _apply_patches(self):
        try:
            _original_session_init = ort.InferenceSession.__init__
            force_provider = settings.FORCE_PROVIDERS
            
            def _patched_session_init(session_self, path_or_bytes, *args, **kwargs):
                available = ort.get_available_providers()
                selected_providers = []
                
                if force_provider == "cuda" and "CUDAExecutionProvider" in available:
                    selected_providers = ["CUDAExecutionProvider"]
                elif force_provider == "coreml" and "CoreMLExecutionProvider" in available:
                    selected_providers = ["CoreMLExecutionProvider"]
                elif force_provider == "metal":
                    if "CoreMLExecutionProvider" in available:
                        selected_providers = ["CoreMLExecutionProvider"]
                    else:
                        logger.warning("Metal/CoreML requested but not available. Falling back to CPU.")
                        selected_providers = ["CPUExecutionProvider"]
                elif force_provider == "cpu":
                    selected_providers = ["CPUExecutionProvider"]
                elif force_provider == "auto":
                    if "CUDAExecutionProvider" in available: selected_providers.append("CUDAExecutionProvider")
                    if "CoreMLExecutionProvider" in available: selected_providers.append("CoreMLExecutionProvider")
                    selected_providers.append("CPUExecutionProvider")
                
                if not selected_providers:
                     selected_providers = ["CPUExecutionProvider"]

                kwargs["providers"] = selected_providers
                logger.debug(f"Patched ORT Session providers: {selected_providers}")
                _original_session_init(session_self, path_or_bytes, *args, **kwargs)

            ort.InferenceSession.__init__ = _patched_session_init
            logger.info(f"Monkey patched ONNX Runtime. Strategy: {force_provider}")
        except Exception as e:
            logger.warning(f"Could not patch onnxruntime: {e}")

    def initialize(self):
        logger.info("Initializing Supertonic TTS Model...")
        kwargs = {}
        if settings.MODEL_THREADS > 0:
            kwargs['intra_op_num_threads'] = settings.MODEL_THREADS
            
        self.model = TTS(auto_download=True, **kwargs)
        logger.info("Supertonic TTS Model initialized.")

    def get_style(self, voice_name: str):
        VOICE_MAP = {
            "alloy": "F1", "echo": "M1", "fable": "M2", "onyx": "M3",
            "nova": "F2", "shimmer": "F3"
        }
        available = getattr(self.model, 'voice_style_names', [])
        target = voice_name if voice_name in available else VOICE_MAP.get(voice_name, available[0] if available else "F1")
        return self.model.get_voice_style(voice_name=target)

    async def _process_chunk(
        self,
        chunk_text: str,
        style,
        speed: float,
        writer: StreamingAudioWriter,
        output_format: str,
        is_last: bool = False,
        normalizer: AudioNormalizer = None,
    ):
        async with self._chunk_semaphore:
            try:
                if is_last:
                    chunk_data = await AudioService.convert_audio(
                        AudioChunk(np.array([], dtype=np.float32), sample_rate=self.model.sample_rate),
                        output_format, writer, speed, "", normalizer=normalizer, is_last_chunk=True,
                    )
                    return chunk_data

                if not chunk_text.strip():
                    return None

                loop = asyncio.get_event_loop()
                logger.debug(f"Synthesizing: textlen={len(chunk_text)}, style={type(style)}, speed={speed}({type(speed)})")
                try:
                    wav, _ = await loop.run_in_executor(
                        None,
                        lambda: self.model.synthesize(chunk_text, style, speed=speed)
                    )
                except Exception as ex:
                    logger.error(f"Synthesize failed: {ex}")
                    raise ex

                logger.debug(f"Synthesized: shape={wav.shape}, dtype={wav.dtype}")

                if wav.ndim == 2 and wav.shape[0] == 1:
                    wav = wav.squeeze()

                audio_chunk = AudioChunk(audio=wav, sample_rate=self.model.sample_rate, text=chunk_text)
                
                logger.debug("Converting audio chunk...")
                return await AudioService.convert_audio(
                    audio_chunk, output_format, writer, speed, chunk_text,
                    is_last_chunk=is_last, normalizer=normalizer,
                )
            except Exception as e:
                logger.error(f"Failed to process chunk: {e}")
                # Print traceback to be sure
                import traceback
                logger.error(traceback.format_exc())
                return None

    async def generate_audio_stream(
        self,
        text: str,
        voice: str,
        writer: StreamingAudioWriter,
        speed: float = 1.0,
        output_format: str = "wav",
        normalization_options: NormalizationOptions = NormalizationOptions(),
    ):
        if not self.model:
            raise RuntimeError("Model not initialized")

        style = self.get_style(voice)
        stream_normalizer = AudioNormalizer()
        stream_normalizer.sample_rate = self.model.sample_rate
        chunk_index = 0

        async for chunk_text, tokens, pause_duration_s in smart_split(text, normalization_options=normalization_options):
            if pause_duration_s and pause_duration_s > 0:
                silence_samples = int(pause_duration_s * self.model.sample_rate)
                silence_audio = np.zeros(silence_samples, dtype=np.int16)
                pause_chunk = AudioChunk(audio=silence_audio, sample_rate=self.model.sample_rate)
                
                formatted_pause = await AudioService.convert_audio(
                    pause_chunk, output_format, writer, speed=speed, 
                    is_last_chunk=False, trim_audio=False, normalizer=stream_normalizer
                )
                if formatted_pause.output:
                    yield formatted_pause
                chunk_index += 1
            elif chunk_text.strip():
                processed = await self._process_chunk(
                    chunk_text, style, speed, writer, output_format,
                    is_last=False, normalizer=stream_normalizer
                )
                if processed and processed.output:
                    yield processed
                chunk_index += 1

        if chunk_index > 0:
            final = await self._process_chunk(
                "", style, speed, writer, output_format,
                is_last=True, normalizer=stream_normalizer
            )
            if final and final.output:
                yield final

    async def generate_audio(self, text, voice, writer, speed=1.0, output_format="wav"):
        audio_chunks = []
        all_output_bytes = bytearray()
        
        async for chunk in self.generate_audio_stream(text, voice, writer, speed, output_format=output_format):
            if chunk.output:
                all_output_bytes.extend(chunk.output)
            if chunk.audio is not None:
                audio_chunks.append(chunk)
                
        combined = AudioChunk.combine(audio_chunks)
        combined.output = bytes(all_output_bytes)
        return combined

# Singleton
tts_service = TTSService()
