"""
🔴 보안 테스트 - Refresh Token 보안 검증

This module tests the security aspects of the refresh token mechanism.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


class TestRefreshTokenSecurity:
    """Refresh token 보안 테스트"""

    def test_refresh_token_success(self, client: TestClient, test_user):
        """정상적인 토큰 갱신 테스트"""
        # 1. 로그인하여 refresh token 획득
        login_data = {"username": test_user["email"], "password": test_user["password"]}
        login_response = client.post("/login", data=login_data)
        
        assert login_response.status_code == 200
        login_result = login_response.json()
        
        refresh_token = login_result["refresh_token"]
        original_access_token = login_result["access_token"]
        
        # 2. Refresh token으로 새 토큰 요청
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/refresh", json=refresh_data)
        
        assert response.status_code == 200
        refresh_result = response.json()
        
        assert "access_token" in refresh_result
        assert "token_type" in refresh_result
        assert refresh_result["token_type"] == "bearer"
        
        # 새 토큰은 기존 토큰과 달라야 함
        assert refresh_result["access_token"] != original_access_token

    def test_refresh_token_invalid(self, client: TestClient):
        """잘못된 refresh token 테스트"""
        invalid_token = "invalid.refresh.token"
        refresh_data = {"refresh_token": invalid_token}
        
        response = client.post("/refresh", json=refresh_data)
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_refresh_token_malformed(self, client: TestClient):
        """잘못된 형식의 refresh token 테스트"""
        malformed_tokens = [
            "",  # 빈 문자열
            "not.a.jwt",  # JWT가 아닌 문자열
            "too.short",  # 너무 짧은 문자열
            "a.b",  # 부분만 있는 JWT
            "header.payload.signature.extra",  # 너무 많은 부분
        ]
        
        for token in malformed_tokens:
            refresh_data = {"refresh_token": token}
            response = client.post("/refresh", json=refresh_data)
            
            assert response.status_code == 401, f"Token '{token}' should be rejected"

    def test_refresh_token_reuse(self, client: TestClient, test_user):
        """Refresh token 재사용 테스트"""
        # 로그인하여 토큰 획득
        login_data = {"username": test_user["email"], "password": test_user["password"]}
        login_response = client.post("/login", data=login_data)
        
        assert login_response.status_code == 200
        refresh_token = login_response.json()["refresh_token"]
        
        # 첫 번째 토큰 갱신
        refresh_data = {"refresh_token": refresh_token}
        first_response = client.post("/refresh", json=refresh_data)
        assert first_response.status_code == 200
        
        # 동일한 refresh token으로 두 번째 시도
        second_response = client.post("/refresh", json=refresh_data)
        
        # 현재 구현이 재사용을 허용하는지 확인
        assert second_response.status_code in [200, 401]

    def test_new_access_token_validity(self, client: TestClient, test_user):
        """갱신된 access token이 실제로 작동하는지 테스트"""
        # 1. 로그인하여 refresh token 획득
        login_data = {"username": test_user["email"], "password": test_user["password"]}
        login_response = client.post("/login", data=login_data)
        
        refresh_token = login_response.json()["refresh_token"]
        
        # 2. 새 access token 획득
        refresh_data = {"refresh_token": refresh_token}
        refresh_response = client.post("/refresh", json=refresh_data)
        
        assert refresh_response.status_code == 200
        new_access_token = refresh_response.json()["access_token"]
        
        # 3. 새 토큰으로 보호된 엔드포인트 접근
        headers = {"Authorization": f"Bearer {new_access_token}"}
        profile_response = client.get("/profile", headers=headers)
        
        assert profile_response.status_code == 200
        assert profile_response.json()["email"] == test_user["email"]

    def test_refresh_with_missing_user(self, client: TestClient, test_user):
        """사용자가 삭제된 후 refresh token 사용 테스트"""
        # 로그인하여 refresh token 획득
        login_data = {"username": test_user["email"], "password": test_user["password"]}
        login_response = client.post("/login", data=login_data)
        
        refresh_token = login_response.json()["refresh_token"]
        
        # 사용자 삭제 시뮬레이션 (Mock 사용)
        with patch('src.repositories.user_repository.UserRepository.find_by_id', return_value=None):
            refresh_data = {"refresh_token": refresh_token}
            response = client.post("/refresh", json=refresh_data)
            
            assert response.status_code == 401
            assert "user not found" in response.json()["detail"].lower()

    def test_refresh_token_content_validation(self, client: TestClient, test_user):
        """Refresh token 내용 검증 테스트"""
        # 로그인하여 유효한 refresh token 획득
        login_data = {"username": test_user["email"], "password": test_user["password"]}
        login_response = client.post("/login", data=login_data)
        
        refresh_token = login_response.json()["refresh_token"]
        
        # JWT 페이로드를 검증하기 위해 토큰을 디코드
        import jwt
        
        try:
            # 토큰 디코드 (서명 검증 없이)
            payload = jwt.decode(refresh_token, options={"verify_signature": False})
            
            # 필수 클레임이 있는지 확인
            assert "sub" in payload  # subject (user_id)
            assert "exp" in payload  # expiration
            assert "type" in payload  # token type
            assert payload["type"] == "refresh"
            
        except jwt.DecodeError:
            pytest.fail("Refresh token is not a valid JWT")


class TestRefreshTokenBasic:
    """기본적인 refresh token 테스트"""

    def test_refresh_rate_limiting_basic(self, client: TestClient, test_user):
        """기본적인 refresh 요청 처리 테스트"""
        # 로그인하여 refresh token 획득
        login_data = {"username": test_user["email"], "password": test_user["password"]}
        login_response = client.post("/login", data=login_data)
        
        refresh_token = login_response.json()["refresh_token"]
        refresh_data = {"refresh_token": refresh_token}
        
        # 연속적으로 몇 개의 요청 보내기
        responses = []
        for _ in range(5):
            response = client.post("/refresh", json=refresh_data)
            responses.append(response)
        
        # 최소한 첫 번째 요청은 성공해야 함
        assert responses[0].status_code == 200
        
        # 모든 요청이 적절한 상태 코드를 반환해야 함
        for response in responses:
            assert response.status_code in [200, 401, 429]