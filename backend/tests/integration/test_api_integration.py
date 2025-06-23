import pytest
from httpx import AsyncClient


class TestAPIIntegration:
    """API 통합 테스트"""

    @pytest.mark.asyncio
    async def test_user_workflow(
        self, async_client: AsyncClient, sample_user_data
    ):
        """사용자 생성 및 조회 워크플로우 테스트"""
        # 1. 사용자 생성
        create_response = await async_client.post(
            "/api/users", json=sample_user_data
        )
        assert create_response.status_code == 200
        created_user = create_response.json()
        assert created_user["created"] is True

        # 2. 생성된 사용자 조회
        user_id = created_user["id"]
        get_response = await async_client.get(f"/api/users/{user_id}")
        assert get_response.status_code == 200
        retrieved_user = get_response.json()
        assert retrieved_user["id"] == user_id

    @pytest.mark.asyncio
    async def test_health_and_root_endpoints(self, async_client: AsyncClient):
        """헬스 체크와 루트 엔드포인트 통합 테스트"""
        # 헬스 체크
        health_response = await async_client.get("/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] == "healthy"

        # 루트 엔드포인트
        root_response = await async_client.get("/")
        assert root_response.status_code == 200
        root_data = root_response.json()
        assert root_data["status"] == "success"

    @pytest.mark.asyncio
    async def test_cors_headers(self, async_client: AsyncClient):
        """CORS 헤더 테스트"""
        response = await async_client.options(
            "/api/users/1",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # CORS preflight 요청이 성공적으로 처리되는지 확인
        assert response.status_code in [200, 204]
