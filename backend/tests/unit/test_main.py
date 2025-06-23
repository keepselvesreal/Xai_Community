from fastapi.testclient import TestClient


class TestMainEndpoints:
    """메인 엔드포인트 단위 테스트"""

    def test_root_endpoint(self, client: TestClient):
        """루트 엔드포인트 테스트"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hello World"
        assert data["status"] == "success"

    def test_health_check_endpoint(self, client: TestClient):
        """헬스 체크 엔드포인트 테스트"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "backend-api"

    def test_get_user_endpoint(self, client: TestClient):
        """사용자 조회 엔드포인트 테스트"""
        user_id = 123
        response = client.get(f"/api/users/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["name"] == f"User {user_id}"
        assert data["email"] == f"user{user_id}@example.com"

    def test_create_user_endpoint(self, client: TestClient, sample_user_data):
        """사용자 생성 엔드포인트 테스트"""
        response = client.post("/api/users", json=sample_user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 123
        assert data["name"] == sample_user_data["name"]
        assert data["email"] == sample_user_data["email"]
        assert data["created"] is True
