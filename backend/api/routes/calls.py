import os
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

router = APIRouter(prefix="/calls", tags=["calls"])


class CallUpdate(BaseModel):
    title: str | None = None
    project_id: int | None = None
    participants: list[str] | None = None


def _build_markdown(call: dict, transcript: dict | None, summary: dict | None) -> str:
    started = call.get("started_at", "")[:10]
    source = call.get("source_app", "")
    duration = call.get("duration_sec") or 0
    mins = duration // 60
    lines = [
        f"# {call.get('title') or 'Chiamata'}",
        "",
        f"**Data:** {started}  **Fonte:** {source}  **Durata:** {mins} min",
        "",
    ]
    if summary:
        lines += ["## Summary", "", summary.get("summary", ""), ""]
        kp = summary.get("key_points") or []
        if kp:
            lines += ["## Key Points", ""] + [f"- {p}" for p in kp] + [""]
        ns = summary.get("next_steps") or []
        if ns:
            lines += ["## Next Steps", ""] + [f"- [ ] {s}" for s in ns] + [""]
        dec = summary.get("decisions") or []
        if dec:
            lines += ["## Decisions", ""] + [f"- {d}" for d in dec] + [""]
    if transcript:
        lines += ["## Transcript", "", transcript.get("full_text", ""), ""]
    return "\n".join(lines)


@router.get("")
async def list_calls(request: Request, project_id: int | None = None, limit: int = 50, offset: int = 0):
    return await request.app.state.db.list_calls(project_id=project_id, limit=limit, offset=offset)


@router.get("/{call_id}")
async def get_call(call_id: int, request: Request):
    db = request.app.state.db
    call = await db.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    transcript = await db.get_transcript(call_id)
    summary = await db.get_summary(call_id)
    return {**call, "transcript": transcript, "summary": summary}


@router.patch("/{call_id}")
async def update_call(call_id: int, body: CallUpdate, request: Request):
    db = request.app.state.db
    call = await db.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    payload = {k: v for k, v in body.model_dump().items() if v is not None}
    await db.update_call(call_id, payload)
    return {"ok": True}


@router.delete("/{call_id}", status_code=204)
async def delete_call(call_id: int, request: Request):
    db = request.app.state.db
    call = await db.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    audio_path = call.get("audio_path")
    if audio_path and os.path.exists(audio_path):
        os.remove(audio_path)
    await db.delete_call(call_id)


@router.get("/{call_id}/export")
async def export_call(call_id: int, request: Request):
    db = request.app.state.db
    call = await db.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    transcript = await db.get_transcript(call_id)
    summary = await db.get_summary(call_id)
    md = _build_markdown(call, transcript, summary)
    title_slug = (call.get("title") or "call").lower().replace(" ", "-")[:40]
    return Response(
        content=md,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{title_slug}.md"'},
    )


@router.get("/{call_id}/audio")
async def stream_audio(call_id: int, request: Request):
    db = request.app.state.db
    call = await db.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    audio_path = call.get("audio_path")
    if not audio_path or not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(audio_path, media_type="audio/wav")


@router.post("/{call_id}/reprocess", status_code=202)
async def reprocess_call(call_id: int, request: Request, background_tasks: BackgroundTasks):
    db = request.app.state.db
    call = await db.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    if call["status"] not in ("error", "done"):
        raise HTTPException(status_code=409, detail=f"Cannot reprocess call with status '{call['status']}'")
    audio_path = call.get("audio_path")
    if not audio_path or not os.path.exists(audio_path):
        raise HTTPException(status_code=422, detail="Audio file not found, cannot reprocess")
    background_tasks.add_task(request.app.state.processing_pipeline, call_id, audio_path)
    return {"ok": True, "message": "Reprocessing started"}
