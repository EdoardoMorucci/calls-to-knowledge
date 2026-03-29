import logging
import threading
import time
import wave
from datetime import datetime
from pathlib import Path
from typing import Optional

import pyaudiowpatch

from backend.config import RecordingConfig

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1024
FORMAT = pyaudiowpatch.paInt16
FLUSH_INTERVAL_SEC = 30


class AudioRecorder:
    def __init__(self, config: RecordingConfig):
        self._config = config
        self._is_recording = False
        self._thread: Optional[threading.Thread] = None
        self._audio_path: Optional[str] = None
        self._stop_event = threading.Event()

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    def start(self, app_name: str) -> None:
        if self._is_recording:
            logger.warning("Recorder already running")
            return
        audio_dir = Path(self._config.audio_dir).expanduser()
        audio_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        safe_app = app_name.replace(".exe", "").lower()
        self._audio_path = str(audio_dir / f"{timestamp}_{safe_app}.wav")
        self._stop_event.clear()
        self._is_recording = True
        self._thread = threading.Thread(
            target=self._record_loop,
            args=(self._audio_path,),
            daemon=True,
            name="AudioRecorder",
        )
        self._thread.start()
        logger.info("Recording started → %s", self._audio_path)

    def stop(self) -> Optional[str]:
        if not self._is_recording:
            return None
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._is_recording = False
        path = self._audio_path
        self._audio_path = None
        logger.info("Recording stopped → %s", path)
        return path

    def _get_loopback_device(self, p: pyaudiowpatch.PyAudio) -> dict:
        """Trova il device loopback WASAPI per il default output device."""
        wasapi_info = p.get_host_api_info_by_type(pyaudiowpatch.paWASAPI)
        default_output = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
        for loopback in p.get_loopback_device_info_generator():
            if default_output["name"] in loopback["name"]:
                return loopback
        # fallback: primo loopback disponibile
        for loopback in p.get_loopback_device_info_generator():
            return loopback
        raise RuntimeError("Nessun device loopback WASAPI trovato")

    def _record_loop(self, audio_path: str) -> None:
        p = pyaudiowpatch.PyAudio()
        try:
            speaker = self._get_loopback_device(p)
            rate = int(speaker["defaultSampleRate"])
            channels = int(speaker["maxInputChannels"])
            logger.info("Loopback device: %s (ch=%d, rate=%d)", speaker["name"], channels, rate)

            stream = p.open(
                format=FORMAT,
                channels=channels,
                rate=rate,
                input=True,
                input_device_index=speaker["index"],
                frames_per_buffer=CHUNK_SIZE,
            )

            frames: list[bytes] = []
            last_flush = time.time()

            with wave.open(audio_path, "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(p.get_sample_size(FORMAT))
                wf.setframerate(rate)

                while not self._stop_event.is_set():
                    data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                    frames.append(data)
                    if time.time() - last_flush >= FLUSH_INTERVAL_SEC:
                        wf.writeframes(b"".join(frames))
                        frames = []
                        last_flush = time.time()

                if frames:
                    wf.writeframes(b"".join(frames))

            stream.stop_stream()
            stream.close()
        except Exception as e:
            logger.error("Recorder error: %s", e)
        finally:
            p.terminate()
