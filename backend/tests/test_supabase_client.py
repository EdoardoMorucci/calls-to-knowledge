import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.db.supabase_client import SupabaseClient


@pytest.mark.asyncio
async def test_create_call_returns_id():
    mock_response = MagicMock()
    mock_response.data = [{"id": 42}]

    mock_table = MagicMock()
    mock_table.insert.return_value.execute = AsyncMock(return_value=mock_response)

    mock_client = MagicMock()
    mock_client.table.return_value = mock_table

    db = SupabaseClient.__new__(SupabaseClient)
    db._client = mock_client

    call_id = await db.create_call(source_app="Teams.exe", trigger="auto")
    assert call_id == 42
    mock_client.table.assert_called_with("calls")


@pytest.mark.asyncio
async def test_update_call_sends_correct_payload():
    mock_response = MagicMock()
    mock_response.data = [{"id": 1}]

    mock_table = MagicMock()
    mock_table.update.return_value.eq.return_value.execute = AsyncMock(return_value=mock_response)

    mock_client = MagicMock()
    mock_client.table.return_value = mock_table

    db = SupabaseClient.__new__(SupabaseClient)
    db._client = mock_client

    await db.update_call(1, {"status": "done", "title": "Test Call"})
    mock_table.update.assert_called_once()
    payload_arg = mock_table.update.call_args[0][0]
    assert payload_arg["status"] == "done"
    assert payload_arg["title"] == "Test Call"
