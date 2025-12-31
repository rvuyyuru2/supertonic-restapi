from dataclasses import dataclass
from typing import Optional, List
import numpy as np

@dataclass
class WordTimestamp:
    word: str
    start_time: float
    end_time: float

@dataclass
class AudioChunk:
    audio: np.ndarray
    sample_rate: int
    text: str = ""
    word_timestamps: Optional[List[WordTimestamp]] = None
    output: Optional[bytes] = None

    @staticmethod
    def combine(chunks: List["AudioChunk"]) -> "AudioChunk":
        if not chunks:
            return AudioChunk(np.array([], dtype=np.float32), 24000)
        
        combined_audio = np.concatenate([c.audio for c in chunks])
        sample_rate = chunks[0].sample_rate
        
        combined_timestamps = []
        offset = 0.0
        for c in chunks:
            if c.word_timestamps:
                for ts in c.word_timestamps:
                    combined_timestamps.append(WordTimestamp(
                        word=ts.word,
                        start_time=ts.start_time + offset,
                        end_time=ts.end_time + offset
                    ))
            offset += len(c.audio) / sample_rate
            
        return AudioChunk(
            audio=combined_audio,
            sample_rate=sample_rate,
            word_timestamps=combined_timestamps if combined_timestamps else None
        )
