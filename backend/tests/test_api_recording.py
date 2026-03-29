import pytest
from unittest.mock import MagicMock
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from backend.api.routes.recording import router
from backend.audio.monitor import AudioMonitor
from backend.audio.state import RecordingState


def make_app(state: RecordingState, monitor: AudioMonitor) -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    app.state.recording_state = state
    app.state.monitor = monitor
    return app


@pytest.mark.asyncio
async def test_status_returns_idle_by_default():
    state = RecordingState()
    app = make_app(state, MagicMock(spec=AudioMonitor))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/recording/status")
    assert response.status_code == 200
    assert response.json()["status"] == "idle"


@pytest.mark.asyncio
async def test_start_calls_monitor_force_start():
    state = RecordingState()
    monitor = MagicMock(spec=AudioMonitor)
    app = make_app(state, monitor)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/recording/start")
    assert response.status_code == 200
    monitor.force_start.assert_called_once_with("manual")


@pytest.mark.asyncio
async def test_stop_calls_monitor_force_stop():
    state = RecordingState()
    state.update(status="recording")
    monitor = MagicMock(spec=AudioMonitor)
    app = make_app(state, monitor)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/recording/stop")
    assert response.status_code == 200
    monitor.force_stop.assert_called_once()


@pytest.mark.asyncio
async def test_stop_when_idle_returns_409():
    state = RecordingState()
    app = make_app(state, MagicMock(spec=AudioMonitor))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/recording/stop")
    assert response.status_code == 409
