from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/recording", tags=["recording"])


@router.get("/status")
async def get_status(request: Request):
    return request.app.state.recording_state.snapshot()


@router.post("/start")
async def start_recording(request: Request):
    state = request.app.state.recording_state
    if state.status == "recording":
        raise HTTPException(status_code=409, detail="Already recording")
    request.app.state.monitor.force_start("manual")
    return {"ok": True}


@router.post("/stop")
async def stop_recording(request: Request):
    state = request.app.state.recording_state
    if state.status != "recording":
        raise HTTPException(status_code=409, detail="Not currently recording")
    request.app.state.monitor.force_stop()
    return {"ok": True}
