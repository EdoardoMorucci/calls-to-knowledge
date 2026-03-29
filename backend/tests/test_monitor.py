import time
from unittest.mock import MagicMock
from backend.audio.monitor import AudioMonitor
from backend.config import RecordingConfig


def make_config(min_seconds: int = 3) -> RecordingConfig:
    return RecordingConfig(
        min_duration_seconds=min_seconds,
        call_apps=["Teams.exe", "chrome.exe"],
        audio_dir="/tmp/audio",
    )


def test_call_start_triggered_after_min_seconds():
    on_start = MagicMock()
    on_end = MagicMock()
    monitor = AudioMonitor(
        config=make_config(min_seconds=3),
        on_call_start=on_start,
        on_call_end=on_end,
        session_provider=MagicMock(return_value="Teams.exe"),
    )
    monitor.start()
    time.sleep(4.2)
    monitor.stop()
    on_start.assert_called_once_with("Teams.exe")
    on_end.assert_not_called()


def test_call_end_triggered_when_audio_stops():
    on_start = MagicMock()
    on_end = MagicMock()
    call_count = {"n": 0}

    def provider():
        call_count["n"] += 1
        return "Teams.exe" if call_count["n"] <= 5 else None

    monitor = AudioMonitor(
        config=make_config(min_seconds=3),
        on_call_start=on_start,
        on_call_end=on_end,
        session_provider=provider,
    )
    monitor.start()
    time.sleep(8)
    monitor.stop()
    on_start.assert_called_once_with("Teams.exe")
    on_end.assert_called_once()


def test_no_trigger_if_audio_stops_before_threshold():
    on_start = MagicMock()
    on_end = MagicMock()
    call_count = {"n": 0}

    def provider():
        call_count["n"] += 1
        return "Teams.exe" if call_count["n"] <= 2 else None

    monitor = AudioMonitor(
        config=make_config(min_seconds=5),
        on_call_start=on_start,
        on_call_end=on_end,
        session_provider=provider,
    )
    monitor.start()
    time.sleep(5)
    monitor.stop()
    on_start.assert_not_called()
    on_end.assert_not_called()


def test_unknown_app_does_not_trigger():
    on_start = MagicMock()
    on_end = MagicMock()
    monitor = AudioMonitor(
        config=make_config(min_seconds=2),
        on_call_start=on_start,
        on_call_end=on_end,
        session_provider=MagicMock(return_value="spotify.exe"),
    )
    monitor.start()
    time.sleep(4)
    monitor.stop()
    on_start.assert_not_called()
