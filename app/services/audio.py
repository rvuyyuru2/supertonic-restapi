import math

import numpy as np
from loguru import logger

from app.core.config import settings
from app.inference.base import AudioChunk
from app.services.streaming_audio_writer import StreamingAudioWriter


class AudioNormalizer:
    """Handles audio normalization state for a single stream"""

    def __init__(self):
        self.chunk_trim_ms = settings.gap_trim_ms
        self.sample_rate = settings.SAMPLE_RATE # Default, should be updated based on model

    @property
    def samples_to_trim(self) -> int:
        return int(self.chunk_trim_ms * self.sample_rate / 1000)

    @property
    def samples_to_pad_start(self) -> int:
        return int(50 * self.sample_rate / 1000)

    def find_first_last_non_silent(
        self,
        audio_data: np.ndarray,
        chunk_text: str,
        speed: float,
        silence_threshold_db: int = -45,
        is_last_chunk: bool = False,
    ) -> tuple[int, int]:
        pad_multiplier = 1
        split_character = chunk_text.strip()
        if len(split_character) > 0:
            split_character = split_character[-1]
            if split_character in settings.dynamic_gap_trim_padding_char_multiplier:
                pad_multiplier = settings.dynamic_gap_trim_padding_char_multiplier[
                    split_character
                ]

        if not is_last_chunk:
            samples_to_pad_end = max(
                int(
                    (
                        settings.dynamic_gap_trim_padding_ms
                        * self.sample_rate
                        * pad_multiplier
                    )
                    / 1000
                )
                - self.samples_to_pad_start,
                0,
            )
        else:
            samples_to_pad_end = self.samples_to_pad_start

        # Use int16 limit for threshold calculation
        amplitude_threshold = 32767 * (10 ** (silence_threshold_db / 20))
        
        non_silent_index_start, non_silent_index_end = None, None

        for X in range(0, len(audio_data)):
            if abs(audio_data[X]) > amplitude_threshold:
                non_silent_index_start = X
                break

        for X in range(len(audio_data) - 1, -1, -1):
            if abs(audio_data[X]) > amplitude_threshold:
                non_silent_index_end = X
                break

        if non_silent_index_start is None or non_silent_index_end is None:
            return 0, len(audio_data)

        return max(non_silent_index_start - self.samples_to_pad_start, 0), min(
            non_silent_index_end + math.ceil(samples_to_pad_end / speed),
            len(audio_data),
        )

    def normalize(self, audio_data: np.ndarray) -> np.ndarray:
        if audio_data.dtype != np.int16:
            return np.clip(audio_data * 32767, -32768, 32767).astype(np.int16)
        return audio_data


class AudioService:
    """Service for audio format conversions with streaming support"""

    SUPPORTED_FORMATS = {"wav", "mp3", "opus", "flac", "aac", "pcm"}

    @staticmethod
    async def convert_audio(
        audio_chunk: AudioChunk,
        output_format: str,
        writer: StreamingAudioWriter,
        speed: float = 1,
        chunk_text: str = "",
        is_last_chunk: bool = False,
        trim_audio: bool = True,
        normalizer: AudioNormalizer = None,
    ) -> AudioChunk:
        try:
            if output_format not in AudioService.SUPPORTED_FORMATS:
                raise ValueError(f"Format {output_format} not supported")

            import asyncio
            loop = asyncio.get_event_loop()

            def _process():
                nonlocal audio_chunk
                inner_normalizer = normalizer
                if inner_normalizer is None:
                    inner_normalizer = AudioNormalizer()
                    inner_normalizer.sample_rate = audio_chunk.sample_rate

                audio_chunk.audio = inner_normalizer.normalize(audio_chunk.audio)

                if trim_audio:
                    audio_chunk = AudioService.trim_audio(
                        audio_chunk, chunk_text, speed, is_last_chunk, inner_normalizer
                    )

                chunk_data = b""
                if len(audio_chunk.audio) > 0:
                    chunk_data = writer.write_chunk(audio_chunk.audio)

                if is_last_chunk:
                    final_data = writer.write_chunk(finalize=True)
                    audio_chunk.output = chunk_data + (final_data if final_data else b"")
                elif chunk_data:
                    audio_chunk.output = chunk_data
                
                return audio_chunk

            return await loop.run_in_executor(None, _process)

        except Exception as e:
            logger.error(f"Error converting audio stream to {output_format}: {str(e)}")
            raise ValueError(f"Failed to convert audio stream to {output_format}: {str(e)}")

    @staticmethod
    def trim_audio(
        audio_chunk: AudioChunk,
        chunk_text: str = "",
        speed: float = 1,
        is_last_chunk: bool = False,
        normalizer: AudioNormalizer = None,
    ) -> AudioChunk:
        if normalizer is None:
            normalizer = AudioNormalizer()
            normalizer.sample_rate = audio_chunk.sample_rate

        audio_chunk.audio = normalizer.normalize(audio_chunk.audio)

        trimmed_samples = 0
        if len(audio_chunk.audio) > (2 * normalizer.samples_to_trim):
            audio_chunk.audio = audio_chunk.audio[
                normalizer.samples_to_trim : -normalizer.samples_to_trim
            ]
            trimmed_samples += normalizer.samples_to_trim

        start_index, end_index = normalizer.find_first_last_non_silent(
            audio_chunk.audio, chunk_text, speed, is_last_chunk=is_last_chunk
        )
        
        start_index = int(start_index)
        end_index = int(end_index)

        audio_chunk.audio = audio_chunk.audio[start_index:end_index]
        trimmed_samples += start_index

        if audio_chunk.word_timestamps is not None:
            for timestamp in audio_chunk.word_timestamps:
                timestamp.start_time -= trimmed_samples / audio_chunk.sample_rate
                timestamp.end_time -= trimmed_samples / audio_chunk.sample_rate
        return audio_chunk
