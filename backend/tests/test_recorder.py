import os
import tempfile
import time
from unittest.mock import MagicMock, patch
from backend.audio.recorder import AudioRecorder
from backend.config import RecordingConfig


def make_config(tmp_dir: str) -> RecordingConfig:
    return RecordingConfig(
        min_duration_seconds=15,
        call_apps=["Teams.exe"],
        audio_dir=tmp_dir,
    )


def test_recorder_creates_wav_file():
    with tempfile.TemporaryDirectory() as tmp_dir:
        config = make_config(tmp_dir)
        recorder = AudioRecorder(config)

        with patch("backend.audio.recorder.pyaudiowpatch") as mock_pa:
            mock_instance = MagicMock()
            mock_pa.PyAudio.return_value = mock_instance
            mock_instance.get_host_api_info_by_type.return_value = {"defaultOutputDevice": 0}
            mock_instance.get_device_info_by_index.return_value = {
                "maxInputChannels": 1,
                "defaultSampleRate": 16000.0,
                "index": 0,
            }
            mock_stream = MagicMock()
            mock_stream.read.return_value = b"\x00\x01" * 512
            mock_instance.open.return_value = mock_stream
            mock_pa.paInt16 = 8
            mock_pa.paWASAPI = 3
            mock_instance.get_sample_size.return_value = 2

            recorder.start("Teams.exe")
            time.sleep(0.3)
            audio_path = recorder.stop()

        assert audio_path is not None
        assert os.path.exists(audio_path)
        assert audio_path.endswith(".wav")


def test_recorder_stop_without_start_returns_none():
    with tempfile.TemporaryDirectory() as tmp_dir:
        recorder = AudioRecorder(make_config(tmp_dir))
        assert recorder.stop() is None


def test_is_recording_flag():
    with tempfile.TemporaryDirectory() as tmp_dir:
        recorder = AudioRecorder(make_config(tmp_dir))
        assert not recorder.is_recording

        with patch("backend.audio.recorder.pyaudiowpatch") as mock_pa:
            mock_instance = MagicMock()
            mock_pa.PyAudio.return_value = mock_instance
            mock_instance.get_host_api_info_by_type.return_value = {"defaultOutputDevice": 0}
            mock_instance.get_device_info_by_index.return_value = {
                "maxInputChannels": 1, "defaultSampleRate": 16000.0, "index": 0,
            }
            mock_stream = MagicMock()
            mock_stream.read.return_value = b"\x00" * 1024
            mock_instance.open.return_value = mock_stream
            mock_pa.paInt16 = 8
            mock_pa.paWASAPI = 3
            mock_instance.get_sample_size.return_value = 2

            recorder.start("Teams.exe")
            assert recorder.is_recording
            recorder.stop()
            assert not recorder.is_recording
