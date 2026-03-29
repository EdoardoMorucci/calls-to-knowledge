import asyncio
import logging
import os
from typing import Any

from openai import AsyncOpenAI

from backend.config import OpenAIConfig, TranscriptionConfig

logger = logging.getLogger(__name__)


class TranscriptionService:
    def __init__(self, openai_config: OpenAIConfig, transcription_config: TranscriptionConfig):
        self._config = transcription_config
        self._openai_config = openai_config

    async def transcribe(self, audio_path: str) -> dict[str, Any]:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        if self._config.provider == "openai":
            return await self._transcribe_openai(audio_path)
        return await self._transcribe_local(audio_path)

    async def _transcribe_openai(self, audio_path: str) -> dict[str, Any]:
        client = AsyncOpenAI(api_key=self._openai_config.api_key)
        with open(audio_path, "rb") as f:
            response = await client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )
        segments = [
            {"start": s.start, "end": s.end, "text": s.text}
            for s in (response.segments or [])
        ]
        return {
            "full_text": response.text,
            "language": response.language,
            "segments": segments,
        }

    async def _transcribe_local(self, audio_path: str) -> dict[str, Any]:
        from faster_whisper import WhisperModel
        model = WhisperModel(self._config.local_model, compute_type="int8")
        loop = asyncio.get_event_loop()
        segments_iter, info = await loop.run_in_executor(
            None, lambda: model.transcribe(audio_path, beam_size=5)
        )
        segments = []
        full_text_parts = []
        for seg in segments_iter:
            segments.append({"start": seg.start, "end": seg.end, "text": seg.text.strip()})
            full_text_parts.append(seg.text.strip())
        return {
            "full_text": " ".join(full_text_parts),
            "language": info.language,
            "segments": segments,
        }
