from pydantic import BaseModel
from typing import Optional, Literal

class OpenAIInput(BaseModel):
    model: str = "tts-1"
    input: str
    voice: str = "alloy"
    response_format: Optional[Literal["mp3", "opus", "aac", "flac", "wav", "pcm"]] = "mp3"
    speed: Optional[float] = 1.0
    stream: bool = False
    normalize: bool = True

class ModelObject(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str
    providers: Optional[list] = None

class ModelList(BaseModel):
    object: str = "list"
    data: list[ModelObject]

class NormalizationOptions(BaseModel):
    remove_silence: bool = True
    normalize_amplitude: bool = True
    target_db: float = -3.0
