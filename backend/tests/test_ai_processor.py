import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from backend.processing.ai_processor import AIProcessor
from backend.config import OpenAIConfig, AIConfig


def make_processor() -> AIProcessor:
    return AIProcessor(
        openai_config=OpenAIConfig(api_key="test-key"),
        ai_config=AIConfig(model="gpt-5-mini"),
    )


SAMPLE_JSON = {
    "title": "Standup 27 Marzo",
    "summary": "Il team ha discusso la roadmap Q2.",
    "key_points": ["Roadmap approvata", "Marco gestisce auth"],
    "next_steps": ["Marco: PR auth entro 10/04"],
    "decisions": ["Usare Supabase come database"],
}


@pytest.mark.asyncio
async def test_process_returns_structured_dict():
    processor = make_processor()

    mock_message = MagicMock()
    mock_message.content = json.dumps(SAMPLE_JSON)
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch("backend.processing.ai_processor.AsyncOpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_client

        result = await processor.process("Testo della trascrizione di prova")

    assert result["title"] == "Standup 27 Marzo"
    assert isinstance(result["key_points"], list)
    assert isinstance(result["next_steps"], list)
    assert isinstance(result["decisions"], list)


@pytest.mark.asyncio
async def test_process_raises_on_empty_transcript():
    processor = make_processor()
    with pytest.raises(ValueError, match="empty"):
        await processor.process("")


def test_prompt_yaml_has_system_key():
    """Verifica che il file YAML del prompt esista e abbia la chiave 'system'."""
    import yaml
    path = Path(__file__).parent.parent / "prompts" / "summary.yaml"
    assert path.exists(), f"Prompt file not found: {path}"
    with open(path) as f:
        data = yaml.safe_load(f)
    assert "system" in data
    assert len(data["system"]) > 50
