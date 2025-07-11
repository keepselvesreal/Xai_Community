"""
보안 미들웨어 단위 테스트

CSP, XSS 방지, CSRF 보호 등 보안 헤더가 올바르게 설정되는지 검증
"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse

from nadle_backend.middleware.security import SecurityHeadersMiddleware


class TestSecurityHeadersMiddleware:
    """보안 헤더 미들웨어 테스트"""

    @pytest.fixture
    def app_with_security_middleware(self):
        """보안 미들웨어가 적용된 테스트 앱"""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        return app

    @pytest.fixture
    def client(self, app_with_security_middleware):
        """테스트 클라이언트"""
        return TestClient(app_with_security_middleware)

    def test_csp_header_added(self, client):
        """CSP 헤더가 올바르게 추가되는지 테스트"""
        response = client.get("/test")
        
        assert response.status_code == 200
        assert "Content-Security-Policy" in response.headers
        
        csp_header = response.headers["Content-Security-Policy"]
        expected_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "img-src 'self' data: https:",
            "font-src 'self' https://fonts.gstatic.com",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        
        for directive in expected_directives:
            assert directive in csp_header

    def test_xss_protection_headers(self, client):
        """XSS 방지 헤더들이 올바르게 설정되는지 테스트"""
        response = client.get("/test")
        
        # X-Content-Type-Options
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        
        # X-Frame-Options
        assert response.headers.get("X-Frame-Options") == "DENY"
        
        # X-XSS-Protection (레거시 브라우저용)
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    def test_hsts_header(self, client):
        """HSTS 헤더가 올바르게 설정되는지 테스트"""
        response = client.get("/test")
        
        hsts_header = response.headers.get("Strict-Transport-Security")
        assert hsts_header is not None
        assert "max-age=31536000" in hsts_header  # 1년
        assert "includeSubDomains" in hsts_header
        assert "preload" in hsts_header

    def test_referrer_policy_header(self, client):
        """Referrer Policy 헤더가 올바르게 설정되는지 테스트"""
        response = client.get("/test")
        
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_permissions_policy_header(self, client):
        """Permissions Policy 헤더가 올바르게 설정되는지 테스트"""
        response = client.get("/test")
        
        permissions_policy = response.headers.get("Permissions-Policy")
        assert permissions_policy is not None
        
        expected_policies = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "accelerometer=()",
            "gyroscope=()",
            "magnetometer=()"
        ]
        
        for policy in expected_policies:
            assert policy in permissions_policy

    def test_security_headers_on_error_responses(self, client):
        """에러 응답에도 보안 헤더가 적용되는지 테스트"""
        response = client.get("/nonexistent")
        
        # 404 응답에도 보안 헤더가 있어야 함
        assert "Content-Security-Policy" in response.headers
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"

    def test_security_headers_on_post_request(self, client):
        """POST 요청에도 보안 헤더가 적용되는지 테스트"""
        response = client.post("/test", json={"data": "test"})
        
        # POST 요청에도 동일한 보안 헤더가 적용되어야 함
        assert "Content-Security-Policy" in response.headers
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_csrf_protection_considerations(self, client):
        """CSRF 보호 관련 헤더 테스트"""
        response = client.get("/test")
        
        # SameSite 쿠키 정책은 쿠키 설정에서 확인
        # CSP의 form-action 지시어로 CSRF 일부 보호
        csp_header = response.headers.get("Content-Security-Policy")
        assert "form-action 'self'" in csp_header


class TestSecurityMiddlewareConfiguration:
    """보안 미들웨어 설정 테스트"""

    def test_environment_specific_csp(self):
        """환경별 CSP 설정 테스트"""
        # 개발 환경에서는 더 느슨한 CSP 정책이 필요할 수 있음
        from nadle_backend.middleware.security import get_csp_policy
        
        dev_policy = get_csp_policy(environment="development")
        prod_policy = get_csp_policy(environment="production")
        
        # 개발 환경에서는 localhost 허용
        assert "localhost" in dev_policy or "127.0.0.1" in dev_policy
        
        # 프로덕션 환경에서는 더 엄격한 정책
        assert prod_policy != dev_policy

    def test_custom_csp_for_api_endpoints(self):
        """API 엔드포인트용 커스텀 CSP 테스트"""
        from nadle_backend.middleware.security import get_api_csp_policy
        
        api_policy = get_api_csp_policy()
        
        # API 응답에는 일반적으로 스크립트나 스타일이 필요 없음
        assert "script-src 'none'" in api_policy or "script-src" not in api_policy