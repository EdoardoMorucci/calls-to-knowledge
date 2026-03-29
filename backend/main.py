import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from backend.audio.monitor import AudioMonitor
from backend.audio.recorder import AudioRecorder
from backend.audio.state import RecordingState
from backend.api.routes.calls import router as calls_router
from backend.api.routes.projects import router as projects_router
from backend.api.routes.recording import router as recording_router
from backend.api.websocket import WebSocketManager
from backend.config import load_config
from backend.db.supabase_client import SupabaseClient
from backend.processing.ai_processor import AIProcessor
from backend.processing.transcription import TranscriptionService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


async def run_processing_pipeline(
    call_id: int,
    audio_path: str,
    db: SupabaseClient,
    transcription: TranscriptionService,
    ai: AIProcessor,
    ws: WebSocketManager,
    state: RecordingState,
) -> None:
    state.update(status="processing")
    await ws.broadcast({"type": "recording_status", "status": "processing", "app": "", "duration_sec": 0})
    try:
        transcript_data = await transcription.transcribe(audio_path)
        await db.save_transcript(
            call_id=call_id,
            full_text=transcript_data["full_text"],
            segments=transcript_data["segments"],
            language=transcript_data["language"],
        )
        summary_data = await ai.process(transcript_data["full_text"])
        await db.save_summary(call_id=call_id, data=summary_data)
        await db.update_call(call_id, {"status": "done", "title": summary_data["title"]})
        await ws.broadcast({"type": "call_ready", "call_id": call_id})
    except Exception as e:
        logger.error("Processing pipeline failed for call %d: %s", call_id, e)
        await db.update_call(call_id, {"status": "error"})
    finally:
        state.reset()
        await ws.broadcast({"type": "recording_status", "status": "idle", "app": "", "duration_sec": 0})


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_config("config.toml")
    db = SupabaseClient(config.supabase)
    await db.connect()

    transcription = TranscriptionService(config.openai, config.transcription)
    ai = AIProcessor(config.openai, config.ai)
    ws_manager = WebSocketManager()
    recording_state = RecordingState()
    recorder = AudioRecorder(config.recording)
    loop = asyncio.get_event_loop()

    async def pipeline(call_id: int, audio_path: str) -> None:
        await run_processing_pipeline(
            call_id, audio_path, db, transcription, ai, ws_manager, recording_state
        )

    def on_call_start(app_name: str) -> None:
        async def _async():
            trigger = "manual" if app_name == "manual" else "auto"
            call_id = await db.create_call(source_app=app_name, trigger=trigger)
            recording_state.update(
                status="recording",
                current_app=app_name,
                current_call_id=call_id,
                duration_sec=0,
            )
            recorder.start(app_name)
            await ws_manager.broadcast(recording_state.to_ws_dict())
        asyncio.run_coroutine_threadsafe(_async(), loop)

    def on_call_end() -> None:
        async def _async():
            audio_path = recorder.stop()
            call_id = recording_state.current_call_id
            if call_id and audio_path:
                await db.update_call(call_id, {
                    "ended_at": datetime.now(timezone.utc).isoformat(),
                    "duration_sec": recording_state.duration_sec,
                    "audio_path": audio_path,
                    "status": "processing",
                })
                await pipeline(call_id, audio_path)
        asyncio.run_coroutine_threadsafe(_async(), loop)

    monitor = AudioMonitor(
        config.recording,
        on_call_start=on_call_start,
        on_call_end=on_call_end,
    )

    async def duration_ticker():
        while True:
            await asyncio.sleep(1)
            if recording_state.status == "recording":
                recording_state.update(duration_sec=recording_state.duration_sec + 1)
                await ws_manager.broadcast(recording_state.to_ws_dict())

    # Startup recovery: chiamate bloccate in status "recording" al riavvio
    stale_calls = await db.get_stale_recording_calls()
    for stale in stale_calls:
        logger.warning("Stale recording call id=%d → marking as error", stale["id"])
        await db.update_call(stale["id"], {"status": "error"})

    monitor.start()
    ticker_task = asyncio.create_task(duration_ticker())

    app.state.db = db
    app.state.monitor = monitor
    app.state.recording_state = recording_state
    app.state.ws_manager = ws_manager
    app.state.processing_pipeline = pipeline

    logger.info("Backend avviato su %s:%d", config.server.host, config.server.port)
    yield

    monitor.stop()
    recorder.stop()
    ticker_task.cancel()


app = FastAPI(title="Calls to Knowledge", lifespan=lifespan)
app.include_router(calls_router)
app.include_router(projects_router)
app.include_router(recording_router)


@app.get("/search")
async def search_not_implemented():
    return {"detail": "Full-text search pianificato per v2"}, 501


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    ws_manager: WebSocketManager = websocket.app.state.ws_manager
    await ws_manager.connect(websocket)
    try:
        state: RecordingState = websocket.app.state.recording_state
        await websocket.send_json(state.to_ws_dict())
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    cfg = load_config("config.toml")
    uvicorn.run("backend.main:app", host=cfg.server.host, port=cfg.server.port, reload=False)
