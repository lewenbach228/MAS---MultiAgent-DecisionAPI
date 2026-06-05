import pytest
from httpx import AsyncClient, ASGITransport
from src.api import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestApi:
    async def test_health(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    async def test_decide_invalid_json(self, client):
        resp = await client.post("/api/decide", json={"foo": "bar"})
        assert resp.status_code == 422

    async def test_decide_missing_fields(self, client):
        resp = await client.post("/api/decide", json={"job": "test"})
        assert resp.status_code == 422

    async def test_get_decision_not_found(self, client):
        resp = await client.get("/api/decide/nonexistent")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Decision not found"
