import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from backend.api.routes.calls import router
from backend.db.supabase_client import SupabaseClient

SAMPLE_CALL = {
    "id": 1, "title": "Standup", "source_app": "Teams.exe",
    "started_at": "2026-03-27T09:32:00Z", "ended_at": "2026-03-27T09:50:00Z",
    "duration_sec": 1080, "status": "done", "project_id": None,
    "participants": [], "recording_trigger": "auto", "updated_at": "2026-03-27T09:50:00Z",
    "audio_path": "/tmp/audio/test.wav",
}
SAMPLE_TRANSCRIPT = {
    "id": 1, "call_id": 1, "full_text": "Ciao a tutti, oggi discutiamo la roadmap.",
    "segments": [], "language": "it",
}
SAMPLE_SUMMARY = {
    "id": 1, "call_id": 1,
    "summary": "Il team ha discusso la roadmap.",
    "key_points": ["Roadmap approvata"],
    "next_steps": ["Marco: PR auth"],
    "decisions": ["Usare Supabase"],
}


def make_app(mock_db: SupabaseClient) -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    app.state.db = mock_db
    app.state.processing_pipeline = AsyncMock()
    return app


@pytest.mark.asyncio
async def test_list_calls_returns_list():
    mock_db = MagicMock(spec=SupabaseClient)
    mock_db.list_calls = AsyncMock(return_value=[SAMPLE_CALL])
    app = make_app(mock_db)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/calls")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_get_call_detail_includes_transcript_and_summary():
    mock_db = MagicMock(spec=SupabaseClient)
    mock_db.get_call = AsyncMock(return_value=SAMPLE_CALL)
    mock_db.get_transcript = AsyncMock(return_value=SAMPLE_TRANSCRIPT)
    mock_db.get_summary = AsyncMock(return_value=SAMPLE_SUMMARY)
    app = make_app(mock_db)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/calls/1")
    data = response.json()
    assert data["title"] == "Standup"
    assert data["transcript"]["full_text"] == "Ciao a tutti, oggi discutiamo la roadmap."
    assert data["summary"]["key_points"] == ["Roadmap approvata"]


@pytest.mark.asyncio
async def test_get_call_not_found_returns_404():
    mock_db = MagicMock(spec=SupabaseClient)
    mock_db.get_call = AsyncMock(return_value=None)
    app = make_app(mock_db)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/calls/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_export_call_returns_markdown():
    mock_db = MagicMock(spec=SupabaseClient)
    mock_db.get_call = AsyncMock(return_value=SAMPLE_CALL)
    mock_db.get_transcript = AsyncMock(return_value=SAMPLE_TRANSCRIPT)
    mock_db.get_summary = AsyncMock(return_value=SAMPLE_SUMMARY)
    app = make_app(mock_db)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/calls/1/export")
    assert response.status_code == 200
    assert "text/markdown" in response.headers["content-type"]
    body = response.text
    assert "# Standup" in body
    assert "## Summary" in body
    assert "## Key Points" in body
    assert "## Next Steps" in body
    assert "## Decisions" in body
    assert "## Transcript" in body


@pytest.mark.asyncio
async def test_patch_call_updates_fields():
    mock_db = MagicMock(spec=SupabaseClient)
    mock_db.get_call = AsyncMock(return_value=SAMPLE_CALL)
    mock_db.update_call = AsyncMock()
    app = make_app(mock_db)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch("/calls/1", json={"title": "Nuovo titolo", "project_id": 2})
    assert response.status_code == 200
    mock_db.update_call.assert_called_once_with(1, {"title": "Nuovo titolo", "project_id": 2})
