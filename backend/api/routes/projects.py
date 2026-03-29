from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None


@router.get("")
async def list_projects(request: Request):
    db = request.app.state.db
    return await db.list_projects()


@router.post("", status_code=201)
async def create_project(body: ProjectCreate, request: Request):
    db = request.app.state.db
    return await db.create_project(name=body.name, description=body.description)


@router.get("/{project_id}")
async def get_project(project_id: int, request: Request):
    db = request.app.state.db
    project = await db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    calls = await db.get_project_calls(project_id)
    total_duration = sum(c.get("duration_sec") or 0 for c in calls)
    all_next_steps = []
    all_decisions = []
    for c in calls:
        for s in c.get("summaries", []):
            for ns in s.get("next_steps", []):
                all_next_steps.append({"text": ns, "call_id": c["id"], "started_at": c["started_at"]})
            for d in s.get("decisions", []):
                all_decisions.append({"text": d, "call_id": c["id"], "started_at": c["started_at"]})
    return {
        **project,
        "calls": calls,
        "total_calls": len(calls),
        "total_duration_sec": total_duration,
        "all_next_steps": all_next_steps,
        "all_decisions": all_decisions,
    }
