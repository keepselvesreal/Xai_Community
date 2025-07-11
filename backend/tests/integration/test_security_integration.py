"""
보안 강화 통합 테스트

전체 보안 시스템의 통합 동작을 검증하는 테스트
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from fastapi import FastAPI, Request, Response, Depends
from unittest.mock import patch, MagicMock

from nadle_backend.middleware.security import SecurityHeadersMiddleware
from nadle_backend.utils.token_security import SecureTokenManager, CSRFProtectionManager
from nadle_backend.services.auth_service import AuthService


@pytest.fixture
def secure_app():
    """보안 미들웨어가 적용된 테스트 앱"""
    app = FastAPI()
    
    # 보안 미들웨어 적용
    app.add_middleware(SecurityHeadersMiddleware, environment="test")
    
    # 테스트용 엔드포인트들
    @app.get("/")
    async def root():
        return {"message": "Hello World"}
    
    @app.post("/login")
    async def login(request: Request, response: Response):
        # 모의 로그인 처리
        auth_service = AuthService()
        user_data = {"user_id": "test_user", "email": "test@example.com"}
        
        try:
            result = await auth_service.login_with_secure_cookies(response, user_data)
            return result
        except Exception as e:
            return {"error": str(e), "message": "Login failed"}
    
    @app.get("/protected")
    async def protected_route(request: Request):
        auth_service = AuthService()
        user_data = await auth_service.verify_token_from_cookie(request)
        
        if not user_data:
            return {"error": "Unauthorized"}, 401
        
        return {"message": "Protected data", "user": user_data}
    
    @app.post("/sensitive-action")
    async def sensitive_action(request: Request):
        auth_service = AuthService()
        
        # 토큰 검증
        user_data = await auth_service.verify_token_from_cookie(request)
        if not user_data:
            return {"error": "Unauthorized"}, 401
        
        # CSRF 검증
        csrf_valid = await auth_service.verify_csrf_token(request)
        if not csrf_valid:
            return {"error": "CSRF validation failed"}, 403
        
        return {"message": "Sensitive action completed"}
    
    @app.post("/logout")
    async def logout(request: Request, response: Response):
        auth_service = AuthService()
        result = await auth_service.logout_with_secure_cookies(request, response)
        return result
    
    return app


@pytest.fixture
def client(secure_app):
    """테스트 클라이언트"""
    return TestClient(secure_app)


class TestSecurityIntegration:
    """보안 강화 통합 테스트"""
    
    def test_security_headers_applied(self, client):
        """보안 헤더가 모든 응답에 적용되는지 테스트"""
        response = client.get("/")
        
        # 기본 보안 헤더 확인
        assert response.headers.get("Content-Security-Policy") is not None
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        
        # Permissions Policy 확인
        permissions_policy = response.headers.get("Permissions-Policy")
        assert permissions_policy is not None
        assert "geolocation=()" in permissions_policy
        assert "microphone=()" in permissions_policy
    
    def test_csp_policy_differentiation(self, client):
        """API와 일반 경로에서 CSP 정책이 다른지 테스트"""
        # 일반 경로
        response = client.get("/")
        general_csp = response.headers.get("Content-Security-Policy")
        
        # API 경로 (시뮬레이션)
        response = client.get("/api/test")  # 404지만 CSP 헤더는 적용됨
        api_csp = response.headers.get("Content-Security-Policy")
        
        # API 경로는 더 엄격한 CSP 적용
        assert general_csp != api_csp
        assert "script-src 'none'" in api_csp or "script-src" not in api_csp
    
    @patch('nadle_backend.services.auth_service.AuthService.create_access_token')
    @patch('nadle_backend.services.auth_service.AuthService.create_refresh_token')
    def test_secure_login_flow(self, mock_refresh_token, mock_access_token, client):
        """보안 로그인 플로우 테스트"""
        # 모의 토큰 설정
        mock_access_token.return_value = "mock_access_token"
        mock_refresh_token.return_value = "mock_refresh_token"
        
        # 로그인 요청
        response = client.post("/login")
        
        # 응답 확인
        assert response.status_code == 200
        
        # 토큰이 응답 본문에 포함되지 않았는지 확인
        response_data = response.json()
        assert "access_token" not in response_data
        assert "refresh_token" not in response_data
        
        # 쿠키 설정 확인
        cookies = response.cookies
        assert "access_token" in cookies
        assert "refresh_token" in cookies
        
        # 보안 속성 확인
        set_cookie_header = response.headers.get("set-cookie")
        assert "HttpOnly" in set_cookie_header
        assert "SameSite=strict" in set_cookie_header
    
    def test_environment_security_validation(self):
        """환경변수 보안 검증 테스트"""
        from nadle_backend.utils.security import verify_environment_security
        
        # 보안 검증 실행
        security_results = verify_environment_security()
        
        # 검증 결과 확인
        assert "overall_status" in security_results
        assert "environment_variables" in security_results
        assert "file_permissions" in security_results
        
        # 심각한 보안 문제가 없는지 확인
        critical_issues = [
            issue for issue in security_results.get("environment_variables", [])
            if issue.get("severity") == "critical"
        ]
        
        if critical_issues:
            pytest.fail(f"Critical security issues found: {critical_issues}")
    
    def test_token_security_best_practices(self):
        """토큰 보안 모범 사례 준수 테스트"""
        from nadle_backend.utils.token_security import TokenExpirationManager, TokenBlacklistManager
        
        # 만료 시간 검증
        expiration_manager = TokenExpirationManager()
        
        access_expiry = expiration_manager.get_access_token_expiry()
        refresh_expiry = expiration_manager.get_refresh_token_expiry()
        
        # Access Token은 짧은 만료 시간
        assert access_expiry.total_seconds() <= 3600  # 1시간 이하
        
        # Refresh Token은 적절한 만료 시간
        assert refresh_expiry.days >= 1  # 최소 1일
        assert refresh_expiry.days <= 30  # 최대 30일
        
        # 블랙리스트 기능 테스트
        blacklist_manager = TokenBlacklistManager()
        test_token = "test_token_for_blacklist"
        
        # 블랙리스트 추가
        blacklist_manager.blacklist_token(test_token)
        
        # 블랙리스트 확인
        assert blacklist_manager.is_token_blacklisted(test_token) is True
        
        # 다른 토큰은 블랙리스트에 없음
        assert blacklist_manager.is_token_blacklisted("other_token") is False
    
    def test_csrf_protection_integration(self):
        """CSRF 보호 통합 테스트"""
        csrf_manager = CSRFProtectionManager()
        
        # CSRF 토큰 생성
        session_id = "test_session_123"
        csrf_token = csrf_manager.generate_csrf_token(session_id)
        
        # 토큰 형식 검증
        assert csrf_token is not None
        assert "." in csrf_token
        
        # 토큰 검증
        assert csrf_manager.verify_csrf_token(csrf_token, session_id) is True
        
        # 잘못된 세션 ID로 검증 실패
        assert csrf_manager.verify_csrf_token(csrf_token, "wrong_session") is False
        
        # 만료된 토큰 검증 실패 (시뮬레이션)
        old_csrf_token = "0000000000.invalid_hash"
        assert csrf_manager.verify_csrf_token(old_csrf_token, session_id) is False
    
    def test_configuration_security_check(self):
        """설정 보안 검증 테스트"""
        from nadle_backend.config import settings
        
        # 민감한 설정 마스킹 테스트
        masked_config = settings.get_masked_config()
        
        # 민감한 필드가 마스킹되었는지 확인
        sensitive_fields = ['secret_key', 'mongodb_url', 'smtp_password']
        
        for field in sensitive_fields:
            if field in masked_config and masked_config[field]:
                # 마스킹된 값에는 "*"가 포함되어야 함
                assert "*" in str(masked_config[field])
        
        # 프로덕션 환경 설정 검증 (시뮬레이션)
        if settings.environment == "production":
            # 프로덕션에서는 디버그 모드 비활성화
            assert settings.debug is False
            
            # 안전한 CORS 설정
            if settings.allowed_origins:
                for origin in settings.allowed_origins:
                    assert "localhost" not in origin
                    assert "127.0.0.1" not in origin
    
    def test_security_middleware_error_handling(self, client):
        """보안 미들웨어 에러 처리 테스트"""
        # 존재하지 않는 엔드포인트 요청 (404)
        response = client.get("/nonexistent")
        
        # 404 응답에도 보안 헤더가 적용되어야 함
        assert response.headers.get("Content-Security-Policy") is not None
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        
        # 서버 오류 시뮬레이션 (500)
        response = client.get("/error")  # 구현되지 않은 엔드포인트
        
        # 오류 응답에도 보안 헤더가 적용되어야 함
        assert response.headers.get("Content-Security-Policy") is not None
    
    @patch('nadle_backend.utils.security.verify_environment_security')
    def test_startup_security_validation(self, mock_verify):
        """애플리케이션 시작 시 보안 검증 테스트"""
        # 보안 검증 결과 모의 설정
        mock_verify.return_value = {
            "overall_status": "secure",
            "environment_variables": [],
            "file_permissions": []
        }
        
        from nadle_backend.config import Settings
        
        # 설정 초기화 시 보안 검증 실행
        test_settings = Settings(
            mongodb_url="mongodb://localhost:27017",
            secret_key="test-secret-key-32-characters-long",
            environment="test",
            environment_security_check=True
        )
        
        # 보안 검증이 호출되었는지 확인
        mock_verify.assert_called_once()
        assert test_settings.environment_security_check is True


class TestSecurityScenarios:
    """보안 시나리오 테스트"""
    
    def test_xss_protection_scenario(self, client):
        """XSS 공격 시나리오 테스트"""
        # 악성 스크립트가 포함된 요청
        malicious_payload = "<script>alert('XSS')</script>"
        
        response = client.post("/", json={"content": malicious_payload})
        
        # CSP 헤더로 스크립트 실행 차단
        csp_header = response.headers.get("Content-Security-Policy")
        assert "script-src 'self'" in csp_header
        
        # X-XSS-Protection 헤더 확인
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    
    def test_csrf_attack_scenario(self, client):
        """CSRF 공격 시나리오 테스트"""
        # CSRF 토큰 없이 민감한 작업 시도
        response = client.post("/sensitive-action")
        
        # CSRF 검증 실패로 요청 차단
        assert response.status_code == 401 or response.status_code == 403
    
    def test_token_hijacking_scenario(self, client):
        """토큰 하이재킹 시나리오 테스트"""
        # HttpOnly 쿠키 사용으로 JavaScript 접근 차단
        response = client.get("/")
        
        set_cookie_header = response.headers.get("set-cookie")
        if set_cookie_header:
            assert "HttpOnly" in set_cookie_header
            assert "Secure" in set_cookie_header
            assert "SameSite=strict" in set_cookie_header


if __name__ == "__main__":
    pytest.main([__file__, "-v"])