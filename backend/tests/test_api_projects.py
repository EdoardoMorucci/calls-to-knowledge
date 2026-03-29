import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from backend.api.routes.projects import router
from backend.db.supabase_client import SupabaseClient


def make_app(mock_db: SupabaseClient) -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    app.state.db = mock_db
    return app


@pytest.mark.asyncio
async def test_list_projects_returns_list():
    mock_db = MagicMock(spec=SupabaseClient)
    mock_db.list_projects = AsyncMock(return_value=[
        {"id": 1, "name": "Alpha", "description": None, "created_at": "2026-03-01T00:00:00Z"},
    ])
    app = make_app(mock_db)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/projects")
    assert response.status_code == 200
    assert response.json()[0]["name"] == "Alpha"


@pytest.mark.asyncio
async def test_create_project_returns_201():
    mock_db = MagicMock(spec=SupabaseClient)
    mock_db.create_project = AsyncMock(return_value={
        "id": 2, "name": "Beta", "description": "Desc", "created_at": "2026-03-01T00:00:00Z"
    })
    app = make_app(mock_db)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/projects", json={"name": "Beta", "description": "Desc"})
    assert response.status_code == 201
    assert response.json()["id"] == 2


@pytest.mark.asyncio
async def test_get_project_not_found_returns_404():
    mock_db = MagicMock(spec=SupabaseClient)
    mock_db.get_project = AsyncMock(return_value=None)
    mock_db.get_project_calls = AsyncMock(return_value=[])
    app = make_app(mock_db)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/projects/999")
    assert response.status_code == 404
