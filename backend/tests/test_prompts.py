import pytest


async def test_list_prompts_empty(client):
    resp = await client.get("/api/prompts")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_create_prompt(client):
    resp = await client.post(
        "/api/prompts",
        json={"name": "Default", "system_prompt": "You are helpful."},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Default"
    assert data["version"] == 1
    assert data["system_prompt"] == "You are helpful."


async def test_auto_version_increment(client):
    await client.post("/api/prompts", json={"name": "Concise", "system_prompt": "v1"})
    resp = await client.post("/api/prompts", json={"name": "Concise", "system_prompt": "v2"})
    assert resp.status_code == 201
    assert resp.json()["version"] == 2


async def test_different_name_starts_at_version_1(client):
    await client.post("/api/prompts", json={"name": "A", "system_prompt": "x"})
    await client.post("/api/prompts", json={"name": "A", "system_prompt": "x"})
    resp = await client.post("/api/prompts", json={"name": "B", "system_prompt": "x"})
    assert resp.json()["version"] == 1


async def test_get_prompt(client):
    prompt_id = (
        await client.post("/api/prompts", json={"name": "P", "system_prompt": "s"})
    ).json()["id"]

    resp = await client.get(f"/api/prompts/{prompt_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == prompt_id


async def test_get_prompt_not_found(client):
    resp = await client.get("/api/prompts/9999")
    assert resp.status_code == 404


async def test_delete_prompt(client):
    prompt_id = (
        await client.post("/api/prompts", json={"name": "P", "system_prompt": "s"})
    ).json()["id"]

    resp = await client.delete(f"/api/prompts/{prompt_id}")
    assert resp.status_code == 204

    resp = await client.get(f"/api/prompts/{prompt_id}")
    assert resp.status_code == 404


async def test_delete_prompt_not_found(client):
    resp = await client.delete("/api/prompts/9999")
    assert resp.status_code == 404
