import pytest


async def test_list_suites_empty(client):
    resp = await client.get("/api/suites")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_create_suite(client):
    resp = await client.post("/api/suites", json={"name": "My Suite", "description": "desc"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My Suite"
    assert data["description"] == "desc"
    assert "id" in data


async def test_create_suite_minimal(client):
    resp = await client.post("/api/suites", json={"name": "Bare"})
    assert resp.status_code == 201
    assert resp.json()["name"] == "Bare"


async def test_get_suite(client):
    create = await client.post("/api/suites", json={"name": "Suite A"})
    suite_id = create.json()["id"]

    resp = await client.get(f"/api/suites/{suite_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == suite_id
    assert data["name"] == "Suite A"
    assert data["cases"] == []


async def test_get_suite_not_found(client):
    resp = await client.get("/api/suites/9999")
    assert resp.status_code == 404


async def test_delete_suite(client):
    create = await client.post("/api/suites", json={"name": "To Delete"})
    suite_id = create.json()["id"]

    resp = await client.delete(f"/api/suites/{suite_id}")
    assert resp.status_code == 204

    resp = await client.get(f"/api/suites/{suite_id}")
    assert resp.status_code == 404


async def test_delete_suite_not_found(client):
    resp = await client.delete("/api/suites/9999")
    assert resp.status_code == 404


async def test_add_case(client):
    suite_id = (await client.post("/api/suites", json={"name": "S"})).json()["id"]

    resp = await client.post(
        f"/api/suites/{suite_id}/cases",
        json={
            "input": "What is 2+2?",
            "expected": "4",
            "criteria": "Correct arithmetic answer",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["input"] == "What is 2+2?"
    assert data["suite_id"] == suite_id


async def test_add_case_suite_not_found(client):
    resp = await client.post(
        "/api/suites/9999/cases",
        json={"input": "x", "expected": "y", "criteria": "z"},
    )
    assert resp.status_code == 404


async def test_suite_detail_includes_cases(client):
    suite_id = (await client.post("/api/suites", json={"name": "S"})).json()["id"]
    await client.post(
        f"/api/suites/{suite_id}/cases",
        json={"input": "a", "expected": "b", "criteria": "c"},
    )
    await client.post(
        f"/api/suites/{suite_id}/cases",
        json={"input": "d", "expected": "e", "criteria": "f"},
    )

    resp = await client.get(f"/api/suites/{suite_id}")
    assert resp.status_code == 200
    assert len(resp.json()["cases"]) == 2


async def test_delete_case(client):
    suite_id = (await client.post("/api/suites", json={"name": "S"})).json()["id"]
    case_id = (
        await client.post(
            f"/api/suites/{suite_id}/cases",
            json={"input": "q", "expected": "a", "criteria": "c"},
        )
    ).json()["id"]

    resp = await client.delete(f"/api/suites/{suite_id}/cases/{case_id}")
    assert resp.status_code == 204

    detail = await client.get(f"/api/suites/{suite_id}")
    assert detail.json()["cases"] == []


async def test_delete_case_not_found(client):
    suite_id = (await client.post("/api/suites", json={"name": "S"})).json()["id"]
    resp = await client.delete(f"/api/suites/{suite_id}/cases/9999")
    assert resp.status_code == 404
