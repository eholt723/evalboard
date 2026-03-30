import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.engine.runner import execute_run
from app.models.run import Run, RunResult
from app.models.suite import TestSuite
from app.schemas.run import RunCreate, RunOut, RunDetail

router = APIRouter(prefix="/runs", tags=["runs"])

# in-process queue store keyed by run_id
_run_queues: dict[int, asyncio.Queue] = {}


@router.post("", response_model=RunOut, status_code=201)
async def create_run(
    payload: RunCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    suite_result = await db.execute(select(TestSuite).where(TestSuite.id == payload.suite_id))
    if not suite_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Suite not found")

    run = Run(
        suite_id=payload.suite_id,
        model_name=payload.model_name,
        prompt_variant_id=payload.prompt_variant_id,
        status="pending",
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    queue: asyncio.Queue = asyncio.Queue()
    _run_queues[run.id] = queue

    background_tasks.add_task(_run_with_new_session, run.id, queue)
    return run


async def _run_with_new_session(run_id: int, queue: asyncio.Queue) -> None:
    from app.db.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        try:
            await execute_run(run_id, session, queue)
        except Exception as exc:
            await queue.put({"type": "error", "detail": str(exc)})


@router.get("/{run_id}/stream")
async def stream_run(run_id: int):
    queue = _run_queues.get(run_id)
    if queue is None:
        # run already finished or doesn't exist — return empty stream
        async def empty():
            yield "data: {\"type\": \"done\"}\n\n"
        return StreamingResponse(empty(), media_type="text/event-stream")

    async def event_generator():
        try:
            while True:
                event = await asyncio.wait_for(queue.get(), timeout=60.0)
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("type") in ("complete", "error"):
                    _run_queues.pop(run_id, None)
                    break
        except asyncio.TimeoutError:
            _run_queues.pop(run_id, None)
            yield "data: {\"type\": \"timeout\"}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("", response_model=list[RunOut])
async def list_runs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Run)
        .options(selectinload(Run.summary))
        .order_by(Run.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{run_id}", response_model=RunDetail)
async def get_run(run_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Run)
        .where(Run.id == run_id)
        .options(selectinload(Run.results), selectinload(Run.summary))
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
