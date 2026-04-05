from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock

import pytest

from app.models.run import Run, RunResult, RunSummary
from app.models.suite import TestSuite
from app.models.case import TestCase


async def _seed(db):
    """Insert two completed runs with known scores for aggregation tests."""
    suite = TestSuite(name="Math Suite")
    db.add(suite)
    await db.flush()

    case = TestCase(suite_id=suite.id, input="2+2", expected="4", criteria="correct")
    db.add(case)
    await db.flush()

    now = datetime.now(timezone.utc)

    run_a = Run(
        suite_id=suite.id,
        model_name="llama-3.1-8b-instant",
        status="completed",
        started_at=now,
        completed_at=now,
    )
    run_b = Run(
        suite_id=suite.id,
        model_name="llama-3.3-70b-versatile",
        status="completed",
        started_at=now,
        completed_at=now,
    )
    db.add_all([run_a, run_b])
    await db.flush()

    db.add(RunResult(run_id=run_a.id, test_case_id=case.id, score=7, pass_=True, latency_ms=100))
    db.add(RunResult(run_id=run_b.id, test_case_id=case.id, score=9, pass_=True, latency_ms=200))

    db.add(RunSummary(run_id=run_a.id, avg_score=7.0, pass_rate=1.0, total_cases=1, completed_cases=1))
    db.add(RunSummary(run_id=run_b.id, avg_score=9.0, pass_rate=1.0, total_cases=1, completed_cases=1))

    await db.commit()
    return suite, run_a, run_b


# --- empty state ---

async def test_recent_runs_empty(client):
    resp = await client.get("/api/dashboard/recent-runs")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_score_trends_empty(client):
    resp = await client.get("/api/dashboard/score-trends")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_leaderboard_empty(client):
    resp = await client.get("/api/dashboard/leaderboard")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_pass_rate_by_suite_empty(client):
    resp = await client.get("/api/dashboard/pass-rate-by-suite")
    assert resp.status_code == 200
    assert resp.json() == []


# --- with data ---

async def test_recent_runs_returns_runs(client, db):
    await _seed(db)

    resp = await client.get("/api/dashboard/recent-runs")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all(r["suite_name"] == "Math Suite" for r in data)
    assert all(r["status"] == "completed" for r in data)


async def test_leaderboard_order(client, db):
    await _seed(db)

    resp = await client.get("/api/dashboard/leaderboard")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    # higher avg_score should come first
    assert data[0]["avg_score"] > data[1]["avg_score"]
    assert data[0]["model_name"] == "llama-3.3-70b-versatile"


async def test_score_trends_chronological(client, db):
    await _seed(db)

    resp = await client.get("/api/dashboard/score-trends")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all("avg_score" in p for p in data)
    assert all("run_id" in p for p in data)


async def test_pass_rate_by_suite(client, db):
    await _seed(db)

    resp = await client.get("/api/dashboard/pass-rate-by-suite")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["suite_name"] == "Math Suite"
    assert data[0]["avg_pass_rate"] == 1.0
    assert data[0]["run_count"] == 2


async def test_compare_runs(client, db):
    _, run_a, run_b = await _seed(db)

    resp = await client.get(f"/api/dashboard/compare/{run_a.id}/{run_b.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["run_a"]["model_name"] == "llama-3.1-8b-instant"
    assert data["run_b"]["model_name"] == "llama-3.3-70b-versatile"
    assert len(data["cases"]) == 1
    assert data["cases"][0]["score_diff"] == 2  # 9 - 7


async def test_compare_runs_not_found(client):
    resp = await client.get("/api/dashboard/compare/9999/8888")
    assert resp.status_code == 404
