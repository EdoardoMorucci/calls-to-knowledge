import os
import tempfile
import pytest
from backend.config import load_config, Config


SAMPLE_TOML = """
[openai]
api_key = "test-key"

[transcription]
provider = "openai"
local_model = "medium"

[ai]
model = "gpt-5-mini"

[supabase]
url = "https://test.supabase.co"
anon_key = "anon-key"
service_role_key = "service-key"

[recording]
min_duration_seconds = 15
call_apps = ["Teams.exe", "chrome.exe"]
audio_dir = "/tmp/audio"

[server]
host = "127.0.0.1"
port = 8000
"""


def test_load_config_returns_config_object():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(SAMPLE_TOML)
        path = f.name
    try:
        config = load_config(path)
        assert isinstance(config, Config)
        assert config.openai.api_key == "test-key"
        assert config.transcription.provider == "openai"
        assert config.ai.model == "gpt-5-mini"
        assert config.supabase.url == "https://test.supabase.co"
        assert config.recording.min_duration_seconds == 15
        assert config.recording.call_apps == ["Teams.exe", "chrome.exe"]
        assert config.server.port == 8000
    finally:
        os.unlink(path)


def test_load_config_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_config("nonexistent.toml")
