import logging
import onnxruntime as ort
from supertonic import TTS
from app.core.config import settings

logger = logging.getLogger("supertonic-api")

class TTSService:
    def __init__(self):
        self.model = None
        self._apply_patches()
        
    def _apply_patches(self):
        # Monkey Patching ORT
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
                    # Metal via CoreML
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
                
                # Default to CPU if empty selection (shouldn't happen with CPU fallback)
                if not selected_providers:
                     selected_providers = ["CPUExecutionProvider"]

                # Force inject
                kwargs["providers"] = selected_providers
                logger.debug(f"Patched ORT Session providers: {selected_providers}")
                
                _original_session_init(session_self, path_or_bytes, *args, **kwargs)

            ort.InferenceSession.__init__ = _patched_session_init
            logger.info(f"Monkey patched ONNX Runtime. Strategy: {force_provider}")
            
        except ImportError:
            logger.warning("Could not patch onnxruntime.")

    def initialize(self):
        logger.info("Initializing Supertonic TTS Model...")
        kwargs = {}
        if settings.MODEL_THREADS > 0:
            kwargs['intra_op_num_threads'] = settings.MODEL_THREADS
            
        self.model = TTS(auto_download=True, **kwargs)
        logger.info("Supertonic TTS Model initialized.")

    def get_style(self, voice_name: str):
        # Resolve voice map or direct
        VOICE_MAP = {
            "alloy": "F1", "echo": "M1", "fable": "M2", "onyx": "M3",
            "nova": "F2", "shimmer": "F3"
        }
        
        available = getattr(self.model, 'voice_style_names', [])
        
        if voice_name in available:
            target = voice_name
        elif voice_name in VOICE_MAP:
            target = VOICE_MAP[voice_name]
        else:
            target = available[0] if available else "F1"
            
        return self.model.get_voice_style(voice_name=target)

    def synthesize(self, text, style, speed, max_chunk_length=settings.MAX_CHUNK_LENGTH):
        return self.model.synthesize(
            text, 
            voice_style=style, 
            speed=speed, 
            max_chunk_length=max_chunk_length,
            silence_duration=0.3
        )

# Singleton
tts_service = TTSService()
