import pytest
from backend.config import (
    Config, OpenAIConfig, TranscriptionConfig, AIConfig,
    SupabaseConfig, RecordingConfig, ServerConfig,
)


@pytest.fixture
def sample_config() -> Config:
    return Config(
        openai=OpenAIConfig(api_key="test-openai-key"),
        transcription=TranscriptionConfig(provider="openai", local_model="medium"),
        ai=AIConfig(model="gpt-5-mini"),
        supabase=SupabaseConfig(
            url="https://test.supabase.co",
            anon_key="anon-key",
            service_role_key="service-key",
        ),
        recording=RecordingConfig(
            min_duration_seconds=15,
            call_apps=["Teams.exe", "chrome.exe"],
            audio_dir="/tmp/audio",
        ),
        server=ServerConfig(host="127.0.0.1", port=8000),
    )
