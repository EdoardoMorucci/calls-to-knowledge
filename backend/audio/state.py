import threading


class RecordingState:
    def __init__(self):
        self.status: str = "idle"          # "idle" | "recording" | "processing"
        self.current_app: str = ""
        self.current_call_id: int | None = None
        self.duration_sec: int = 0
        self._lock = threading.Lock()

    def update(self, **kwargs) -> None:
        with self._lock:
            for key, value in kwargs.items():
                setattr(self, key, value)

    def reset(self) -> None:
        with self._lock:
            self.status = "idle"
            self.current_app = ""
            self.current_call_id = None
            self.duration_sec = 0

    def to_ws_dict(self) -> dict:
        with self._lock:
            return {
                "type": "recording_status",
                "status": self.status,
                "app": self.current_app,
                "duration_sec": self.duration_sec,
            }

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "status": self.status,
                "app": self.current_app,
                "duration_sec": self.duration_sec,
            }
