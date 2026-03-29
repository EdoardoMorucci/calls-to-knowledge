import tomllib
from dataclasses import dataclass


@dataclass
class OpenAIConfig:
    api_key: str


@dataclass
class TranscriptionConfig:
    provider: str
    local_model: str


@dataclass
class AIConfig:
    model: str


@dataclass
class SupabaseConfig:
    url: str
    anon_key: str
    service_role_key: str


@dataclass
class RecordingConfig:
    min_duration_seconds: int
    call_apps: list[str]
    audio_dir: str


@dataclass
class ServerConfig:
    host: str
    port: int


@dataclass
class Config:
    openai: OpenAIConfig
    transcription: TranscriptionConfig
    ai: AIConfig
    supabase: SupabaseConfig
    recording: RecordingConfig
    server: ServerConfig


def load_config(path: str = "config.toml") -> Config:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    return Config(
        openai=OpenAIConfig(**data["openai"]),
        transcription=TranscriptionConfig(**data["transcription"]),
        ai=AIConfig(**data["ai"]),
        supabase=SupabaseConfig(**data["supabase"]),
        recording=RecordingConfig(**data["recording"]),
        server=ServerConfig(**data["server"]),
    )
