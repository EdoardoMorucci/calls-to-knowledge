import logging
import threading
import time
from typing import Callable

from backend.config import RecordingConfig

logger = logging.getLogger(__name__)


def _default_session_provider(call_apps: list[str]) -> str | None:
    """Interroga WASAPI tramite pycaw e restituisce il nome del processo se ha audio attivo."""
    try:
        from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            if session.Process is None:
                continue
            name = session.Process.name()
            if name.lower() in [app.lower() for app in call_apps]:
                try:
                    meter = session._ctl.QueryInterface(IAudioMeterInformation)
                    if meter.GetPeakValue() > 0.01:
                        return name
                except Exception:
                    continue
    except Exception as e:
        logger.debug("WASAPI session query failed: %s", e)
    return None


class AudioMonitor:
    def __init__(
        self,
        config: RecordingConfig,
        on_call_start: Callable[[str], None],
        on_call_end: Callable[[], None],
        session_provider: Callable[[], str | None] | None = None,
    ):
        self._config = config
        self._on_call_start = on_call_start
        self._on_call_end = on_call_end
        self._session_provider = session_provider or (
            lambda: _default_session_provider(config.call_apps)
        )
        self._consecutive_seconds = 0
        self._in_call = False
        self._is_running = False
        self._thread: threading.Thread | None = None

    def _loop(self) -> None:
        while self._is_running:
            app = self._session_provider()
            if app and app.lower() in [a.lower() for a in self._config.call_apps]:
                self._consecutive_seconds += 1
                if (
                    not self._in_call
                    and self._consecutive_seconds >= self._config.min_duration_seconds
                ):
                    self._in_call = True
                    logger.info("Call detected from %s", app)
                    self._on_call_start(app)
            else:
                if self._in_call:
                    logger.info("Call ended")
                    self._in_call = False
                    self._on_call_end()
                self._consecutive_seconds = 0
            time.sleep(1)

    def start(self) -> None:
        self._is_running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="AudioMonitor")
        self._thread.start()

    def stop(self) -> None:
        self._is_running = False
        if self._thread:
            self._thread.join(timeout=3)

    def force_start(self, app: str) -> None:
        """Override manuale: simula il rilevamento di una chiamata."""
        if not self._in_call:
            self._in_call = True
            self._on_call_start(app)

    def force_stop(self) -> None:
        """Override manuale: simula la fine di una chiamata."""
        if self._in_call:
            self._in_call = False
            self._consecutive_seconds = 0
            self._on_call_end()
