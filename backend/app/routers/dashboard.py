from fastapi import APIRouter, Depends
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.db.database import get_db
from app.models.run import Run, RunSummary
from app.models.suite import TestSuite

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class RecentRunOut(BaseModel):
    run_id: int
    suite_name: str
    model_name: str
    status: str
    avg_score: float | None
    pass_rate: float | None
    total_cases: int
    completed_cases: int

    model_config = {"from_attributes": True}


class ScoreTrendPoint(BaseModel):
    run_id: int
    model_name: str
    suite_name: str
    avg_score: float | None
    pass_rate: float | None
    started_at: str  # ISO string


class ModelLeaderboardEntry(BaseModel):
    model_name: str
    avg_score: float
    avg_pass_rate: float
    run_count: int


class PassRateBySuite(BaseModel):
    suite_name: str
    avg_pass_rate: float
    run_count: int


@router.get("/recent-runs", response_model=list[RecentRunOut])
async def recent_runs(limit: int = 10, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Run, RunSummary, TestSuite)
        .join(RunSummary, RunSummary.run_id == Run.id, isouter=True)
        .join(TestSuite, TestSuite.id == Run.suite_id)
        .order_by(desc(Run.created_at))
        .limit(limit)
    )
    rows = result.all()
    out = []
    for run, summary, suite in rows:
        out.append(RecentRunOut(
            run_id=run.id,
            suite_name=suite.name,
            model_name=run.model_name,
            status=run.status,
            avg_score=summary.avg_score if summary else None,
            pass_rate=summary.pass_rate if summary else None,
            total_cases=summary.total_cases if summary else 0,
            completed_cases=summary.completed_cases if summary else 0,
        ))
    return out


@router.get("/score-trends", response_model=list[ScoreTrendPoint])
async def score_trends(suite_id: int | None = None, limit: int = 30, db: AsyncSession = Depends(get_db)):
    query = (
        select(Run, RunSummary, TestSuite)
        .join(RunSummary, RunSummary.run_id == Run.id)
        .join(TestSuite, TestSuite.id == Run.suite_id)
        .where(Run.status == "completed")
    )
    if suite_id:
        query = query.where(Run.suite_id == suite_id)
    query = query.order_by(desc(Run.started_at)).limit(limit)

    result = await db.execute(query)
    rows = result.all()
    return [
        ScoreTrendPoint(
            run_id=run.id,
            model_name=run.model_name,
            suite_name=suite.name,
            avg_score=summary.avg_score,
            pass_rate=summary.pass_rate,
            started_at=run.started_at.isoformat(),
        )
        for run, summary, suite in reversed(rows)  # chronological order
    ]


@router.get("/leaderboard", response_model=list[ModelLeaderboardEntry])
async def leaderboard(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            Run.model_name,
            func.avg(RunSummary.avg_score).label("avg_score"),
            func.avg(RunSummary.pass_rate).label("avg_pass_rate"),
            func.count(Run.id).label("run_count"),
        )
        .join(RunSummary, RunSummary.run_id == Run.id)
        .where(Run.status == "completed")
        .group_by(Run.model_name)
        .order_by(desc("avg_score"))
    )
    rows = result.all()
    return [
        ModelLeaderboardEntry(
            model_name=row.model_name,
            avg_score=round(row.avg_score, 2),
            avg_pass_rate=round(row.avg_pass_rate, 2),
            run_count=row.run_count,
        )
        for row in rows
    ]


@router.get("/pass-rate-by-suite", response_model=list[PassRateBySuite])
async def pass_rate_by_suite(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            TestSuite.name,
            func.avg(RunSummary.pass_rate).label("avg_pass_rate"),
            func.count(Run.id).label("run_count"),
        )
        .join(Run, Run.suite_id == TestSuite.id)
        .join(RunSummary, RunSummary.run_id == Run.id)
        .where(Run.status == "completed")
        .group_by(TestSuite.name)
        .order_by(desc("avg_pass_rate"))
    )
    rows = result.all()
    return [
        PassRateBySuite(
            suite_name=row.name,
            avg_pass_rate=round(row.avg_pass_rate, 2),
            run_count=row.run_count,
        )
        for row in rows
    ]


@router.get("/compare/{run_a_id}/{run_b_id}")
async def compare_runs(run_a_id: int, run_b_id: int, db: AsyncSession = Depends(get_db)):
    from app.models.run import RunResult
    from app.models.case import TestCase

    async def load_run(run_id: int):
        r = await db.execute(
            select(Run)
            .where(Run.id == run_id)
            .options(selectinload(Run.results), selectinload(Run.summary))
        )
        return r.scalar_one_or_none()

    run_a, run_b = await load_run(run_a_id), await load_run(run_b_id)
    if not run_a or not run_b:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="One or both runs not found")

    # index results by test_case_id
    a_by_case = {r.test_case_id: r for r in run_a.results}
    b_by_case = {r.test_case_id: r for r in run_b.results}
    case_ids = sorted(set(a_by_case) | set(b_by_case))

    cases_result = await db.execute(
        select(TestCase).where(TestCase.id.in_(case_ids))
    )
    cases = {c.id: c for c in cases_result.scalars().all()}

    comparison = []
    for case_id in case_ids:
        a_r = a_by_case.get(case_id)
        b_r = b_by_case.get(case_id)
        case = cases.get(case_id)
        comparison.append({
            "test_case_id": case_id,
            "input": case.input if case else None,
            "expected": case.expected if case else None,
            "run_a": {
                "score": a_r.score if a_r else None,
                "pass": a_r.pass_ if a_r else None,
                "reasoning": a_r.reasoning if a_r else None,
                "latency_ms": a_r.latency_ms if a_r else None,
            },
            "run_b": {
                "score": b_r.score if b_r else None,
                "pass": b_r.pass_ if b_r else None,
                "reasoning": b_r.reasoning if b_r else None,
                "latency_ms": b_r.latency_ms if b_r else None,
            },
            "score_diff": (b_r.score - a_r.score) if (a_r and b_r and a_r.score is not None and b_r.score is not None) else None,
        })

    return {
        "run_a": {
            "id": run_a.id,
            "model_name": run_a.model_name,
            "avg_score": run_a.summary.avg_score if run_a.summary else None,
            "pass_rate": run_a.summary.pass_rate if run_a.summary else None,
        },
        "run_b": {
            "id": run_b.id,
            "model_name": run_b.model_name,
            "avg_score": run_b.summary.avg_score if run_b.summary else None,
            "pass_rate": run_b.summary.pass_rate if run_b.summary else None,
        },
        "cases": comparison,
    }
