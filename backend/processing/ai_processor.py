import json
import logging
from pathlib import Path
from typing import Any

import yaml
from openai import AsyncOpenAI

from backend.config import AIConfig, OpenAIConfig

logger = logging.getLogger(__name__)

_PROMPTS_PATH = Path(__file__).parent.parent / "prompts" / "summary.yaml"


def _load_system_prompt() -> str:
    with open(_PROMPTS_PATH) as f:
        data = yaml.safe_load(f)
    return data["system"]


class AIProcessor:
    def __init__(self, openai_config: OpenAIConfig, ai_config: AIConfig):
        self._openai_config = openai_config
        self._ai_config = ai_config
        self._system_prompt = _load_system_prompt()

    async def process(self, transcript: str) -> dict[str, Any]:
        if not transcript.strip():
            raise ValueError("Cannot process empty transcript")
        client = AsyncOpenAI(api_key=self._openai_config.api_key)
        response = await client.chat.completions.create(
            model=self._ai_config.model,
            messages=[
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": f"Trascrizione:\n\n{transcript}"},
            ],
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error("AI response is not valid JSON: %s", raw)
            raise ValueError(f"Invalid JSON from AI: {e}") from e
        return {
            "title": data.get("title", ""),
            "summary": data.get("summary", ""),
            "key_points": data.get("key_points", []),
            "next_steps": data.get("next_steps", []),
            "decisions": data.get("decisions", []),
        }
