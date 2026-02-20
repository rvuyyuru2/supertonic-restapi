from pydantic import BaseModel, Field
from typing import Optional, Literal


class OpenAIInput(BaseModel):
    """OpenAI-compatible TTS input schema."""
    model: str = Field(default="tts-1", description="TTS model to use")
    input: str = Field(..., description="Text to convert to speech")
    voice: str = Field(default="alloy", description="Voice to use for synthesis")
    response_format: Optional[Literal["mp3", "opus", "aac", "flac", "wav", "pcm"]] = Field(
        default="mp3", description="Output audio format"
    )
    speed: Optional[float] = Field(default=1.0, ge=0.25, le=4.0, description="Speech speed multiplier")
    normalize: bool = Field(default=True, description="Whether to normalize text before synthesis")


class ModelObject(BaseModel):
    """Model object for /v1/models endpoint."""
    id: str
    object: str = "model"
    created: int
    owned_by: str
    providers: Optional[list] = None


class ModelList(BaseModel):
    """List of models for /v1/models endpoint."""
    object: str = "list"
    data: list[ModelObject]
