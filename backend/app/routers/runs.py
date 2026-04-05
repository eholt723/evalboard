import asyncio
import json
from datetime import datetime

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


class RunBroadcaster:
    """Fan-out SSE events to all connected clients for a run."""

    def __init__(self):
        self._subscribers: dict[int, list[asyncio.Queue]] = {}
        self._history: dict[int, list[dict]] = {}
        self._done: set[int] = set()

    def subscribe(self, run_id: int) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        if run_id not in self._subscribers:
            self._subscribers[run_id] = []
        self._subscribers[run_id].append(q)
        # replay history so reconnecting clients catch up
        for event in self._history.get(run_id, []):
            q.put_nowait(event)
        return q

    def unsubscribe(self, run_id: int, q: asyncio.Queue) -> None:
        subs = self._subscribers.get(run_id, [])
        if q in subs:
            subs.remove(q)

    async def publish(self, run_id: int, event: dict) -> None:
        self._history.setdefault(run_id, []).append(event)
        for q in list(self._subscribers.get(run_id, [])):
            await q.put(event)
        if event.get("type") in ("complete", "error"):
            self._done.add(run_id)

    def is_done(self, run_id: int) -> bool:
        return run_id in self._done

    def cleanup(self, run_id: int) -> None:
        self._subscribers.pop(run_id, None)
        self._history.pop(run_id, None)
        self._done.discard(run_id)


broadcaster = RunBroadcaster()


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

    # Re-fetch with selectinload so Pydantic doesn't trigger a lazy load on
    # the summary relationship (which raises MissingGreenlet in async context).
    result = await db.execute(
        select(Run).where(Run.id == run.id).options(selectinload(Run.summary))
    )
    run = result.scalar_one()

    background_tasks.add_task(_run_with_new_session, run.id)
    return run


async def _run_with_new_session(run_id: int) -> None:
    from app.db.database import AsyncSessionLocal

    async def publish(event: dict):
        await broadcaster.publish(run_id, event)

    async with AsyncSessionLocal() as session:
        try:
            await execute_run(run_id, session, publish)
        except Exception as exc:
            await broadcaster.publish(run_id, {"type": "error", "detail": str(exc)})


@router.get("/{run_id}/stream")
async def stream_run(run_id: int, db: AsyncSession = Depends(get_db)):
    # verify run exists
    result = await db.execute(select(Run).where(Run.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # if run already finished and we have no history, pull results from DB
    if broadcaster.is_done(run_id) or run.status == "completed":
        async def replay_from_db():
            res = await db.execute(
                select(RunResult).where(RunResult.run_id == run_id).order_by(RunResult.id)
            )
            results = res.scalars().all()
            for i, r in enumerate(results, 1):
                event = {
                    "type": "result",
                    "index": i,
                    "total": len(results),
                    "test_case_id": r.test_case_id,
                    "run_result_id": r.id,
                    "score": r.score,
                    "pass": r.pass_,
                    "latency_ms": r.latency_ms,
                }
                yield f"data: {json.dumps(event)}\n\n"
            yield f"data: {{\"type\": \"done\"}}\n\n"

        return StreamingResponse(replay_from_db(), media_type="text/event-stream")

    q = broadcaster.subscribe(run_id)

    async def event_generator():
        try:
            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=120.0)
                except asyncio.TimeoutError:
                    yield "data: {\"type\": \"keepalive\"}\n\n"
                    continue
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("type") in ("complete", "error", "done"):
                    break
        finally:
            broadcaster.unsubscribe(run_id, q)

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
