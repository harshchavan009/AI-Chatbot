import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_health_check():
    """
    Test the health check endpoint.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
async def test_chat_endpoint_validation():
    """
    Test that the chat endpoint validates input correctly.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Test missing user_input
        response = await ac.post("/api/chat", json={"session_id": "test"})
    assert response.status_code == 422
