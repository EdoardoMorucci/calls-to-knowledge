import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.processing.transcription import TranscriptionService
from backend.config import OpenAIConfig, TranscriptionConfig


def make_service(provider: str = "openai") -> TranscriptionService:
    return TranscriptionService(
        openai_config=OpenAIConfig(api_key="test-key"),
        transcription_config=TranscriptionConfig(provider=provider, local_model="medium"),
    )


@pytest.mark.asyncio
async def test_openai_transcription_returns_structured_result():
    service = make_service("openai")

    mock_segment = MagicMock()
    mock_segment.start = 0.0
    mock_segment.end = 5.0
    mock_segment.text = "Ciao a tutti."

    mock_response = MagicMock()
    mock_response.text = "Ciao a tutti."
    mock_response.language = "it"
    mock_response.segments = [mock_segment]

    with patch("backend.processing.transcription.AsyncOpenAI") as mock_cls, \
         patch("backend.processing.transcription.os.path.exists", return_value=True), \
         patch("builtins.open", MagicMock()):
        mock_client = MagicMock()
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_client

        result = await service.transcribe("/tmp/fake_existing.wav")

    assert result["full_text"] == "Ciao a tutti."
    assert result["language"] == "it"
    assert result["segments"] == [{"start": 0.0, "end": 5.0, "text": "Ciao a tutti."}]


@pytest.mark.asyncio
async def test_transcription_raises_on_missing_file():
    service = make_service("openai")
    with pytest.raises(FileNotFoundError):
        await service.transcribe("/tmp/nonexistent_xyz_abc.wav")
