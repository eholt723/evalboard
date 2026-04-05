from unittest.mock import patch, AsyncMock
import pytest


async def _make_suite(client):
    return (await client.post("/api/suites", json={"name": "S"})).json()["id"]


async def test_list_runs_empty(client):
    resp = await client.get("/api/runs")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_create_run(client):
    suite_id = await _make_suite(client)

    with patch("app.routers.runs._run_with_new_session", new_callable=AsyncMock):
        resp = await client.post(
            "/api/runs",
            json={"suite_id": suite_id, "model_name": "llama-3.1-8b-instant"},
        )

    assert resp.status_code == 201
    data = resp.json()
    assert data["suite_id"] == suite_id
    assert data["model_name"] == "llama-3.1-8b-instant"
    assert data["status"] == "pending"


async def test_create_run_with_prompt_variant(client):
    suite_id = await _make_suite(client)
    prompt_id = (
        await client.post("/api/prompts", json={"name": "P", "system_prompt": "s"})
    ).json()["id"]

    with patch("app.routers.runs._run_with_new_session", new_callable=AsyncMock):
        resp = await client.post(
            "/api/runs",
            json={
                "suite_id": suite_id,
                "model_name": "llama-3.3-70b-versatile",
                "prompt_variant_id": prompt_id,
            },
        )

    assert resp.status_code == 201
    assert resp.json()["prompt_variant_id"] == prompt_id


async def test_create_run_suite_not_found(client):
    with patch("app.routers.runs._run_with_new_session", new_callable=AsyncMock):
        resp = await client.post(
            "/api/runs",
            json={"suite_id": 9999, "model_name": "llama-3.1-8b-instant"},
        )
    assert resp.status_code == 404


async def test_get_run(client):
    suite_id = await _make_suite(client)

    with patch("app.routers.runs._run_with_new_session", new_callable=AsyncMock):
        run_id = (
            await client.post(
                "/api/runs",
                json={"suite_id": suite_id, "model_name": "llama-3.1-8b-instant"},
            )
        ).json()["id"]

    resp = await client.get(f"/api/runs/{run_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == run_id
    assert data["results"] == []


async def test_get_run_not_found(client):
    resp = await client.get("/api/runs/9999")
    assert resp.status_code == 404


async def test_list_runs_returns_created(client):
    suite_id = await _make_suite(client)

    with patch("app.routers.runs._run_with_new_session", new_callable=AsyncMock):
        await client.post(
            "/api/runs",
            json={"suite_id": suite_id, "model_name": "llama-3.1-8b-instant"},
        )
        await client.post(
            "/api/runs",
            json={"suite_id": suite_id, "model_name": "llama-3.3-70b-versatile"},
        )

    resp = await client.get("/api/runs")
    assert resp.status_code == 200
    assert len(resp.json()) == 2
