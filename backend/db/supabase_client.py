from datetime import datetime, timezone
from supabase import acreate_client, AsyncClient
from backend.config import SupabaseConfig


class SupabaseClient:
    def __init__(self, config: SupabaseConfig):
        self._config = config
        self._client: AsyncClient | None = None

    async def connect(self) -> None:
        self._client = await acreate_client(
            self._config.url,
            self._config.service_role_key,
        )

    # --- Calls ---

    async def create_call(self, source_app: str, trigger: str = "auto") -> int:
        result = await self._client.table("calls").insert({
            "source_app": source_app,
            "recording_trigger": trigger,
            "status": "recording",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        return result.data[0]["id"]

    async def update_call(self, call_id: int, payload: dict) -> None:
        payload = {**payload, "updated_at": datetime.now(timezone.utc).isoformat()}
        await self._client.table("calls").update(payload).eq("id", call_id).execute()

    async def get_call(self, call_id: int) -> dict | None:
        result = await self._client.table("calls").select("*").eq("id", call_id).execute()
        return result.data[0] if result.data else None

    async def list_calls(self, project_id: int | None = None, limit: int = 50, offset: int = 0) -> list[dict]:
        query = (
            self._client.table("calls")
            .select("*, summaries(summary)")
            .order("started_at", desc=True)
            .limit(limit)
            .offset(offset)
        )
        if project_id is not None:
            query = query.eq("project_id", project_id)
        result = await query.execute()
        return result.data

    async def delete_call(self, call_id: int) -> dict | None:
        result = await self._client.table("calls").delete().eq("id", call_id).execute()
        return result.data[0] if result.data else None

    async def get_stale_recording_calls(self) -> list[dict]:
        result = await self._client.table("calls").select("*").eq("status", "recording").execute()
        return result.data

    # --- Transcripts ---

    async def save_transcript(self, call_id: int, full_text: str, segments: list, language: str) -> None:
        await self._client.table("transcripts").insert({
            "call_id": call_id,
            "full_text": full_text,
            "segments": segments,
            "language": language,
        }).execute()

    async def get_transcript(self, call_id: int) -> dict | None:
        result = await self._client.table("transcripts").select("*").eq("call_id", call_id).execute()
        return result.data[0] if result.data else None

    # --- Summaries ---

    async def save_summary(self, call_id: int, data: dict) -> None:
        await self._client.table("summaries").insert({
            "call_id": call_id,
            "summary": data.get("summary", ""),
            "key_points": data.get("key_points", []),
            "next_steps": data.get("next_steps", []),
            "decisions": data.get("decisions", []),
        }).execute()

    async def get_summary(self, call_id: int) -> dict | None:
        result = await self._client.table("summaries").select("*").eq("call_id", call_id).execute()
        return result.data[0] if result.data else None

    # --- Projects ---

    async def create_project(self, name: str, description: str | None = None) -> dict:
        result = await self._client.table("projects").insert({
            "name": name,
            "description": description,
        }).execute()
        return result.data[0]

    async def list_projects(self) -> list[dict]:
        result = await self._client.table("projects").select("*").order("created_at", desc=True).execute()
        return result.data

    async def get_project(self, project_id: int) -> dict | None:
        result = await self._client.table("projects").select("*").eq("id", project_id).execute()
        return result.data[0] if result.data else None

    async def get_project_calls(self, project_id: int) -> list[dict]:
        result = (
            await self._client.table("calls")
            .select("*, summaries(next_steps, decisions)")
            .eq("project_id", project_id)
            .order("started_at", desc=True)
            .execute()
        )
        return result.data
