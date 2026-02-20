from dataclasses import dataclass
from typing import Optional, List
import numpy as np


@dataclass
class AudioChunk:
    """Represents a chunk of audio data with metadata."""
    audio: np.ndarray
    sample_rate: int
    text: str = ""
    output: Optional[bytes] = None

    @staticmethod
    def combine(chunks: List["AudioChunk"]) -> "AudioChunk":
        """Combine multiple audio chunks into one."""
        if not chunks:
            return AudioChunk(np.array([], dtype=np.float32), 24000)
        
        combined_audio = np.concatenate([c.audio for c in chunks])
        sample_rate = chunks[0].sample_rate
        
        return AudioChunk(
            audio=combined_audio,
            sample_rate=sample_rate,
        )
