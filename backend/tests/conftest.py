import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from backend.main import app


@pytest.fixture
def client():
    """동기 테스트 클라이언트"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client():
    """비동기 테스트 클라이언트"""
    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_user_data():
    """샘플 사용자 데이터"""
    return {"name": "Test User", "email": "test@example.com"}
