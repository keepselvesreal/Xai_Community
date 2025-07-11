"""
토큰 저장 보안 테스트

JWT 토큰의 안전한 저장과 전송을 위한 HttpOnly 쿠키 및 보안 설정 테스트
"""

import pytest
from datetime import datetime, timedelta
from fastapi import FastAPI, Response
from fastapi.testclient import TestClient
from unittest.mock import patch

from nadle_backend.services.auth_service import AuthService
from nadle_backend.utils.token_security import SecureTokenManager


class TestSecureTokenManager:
    """보안 토큰 매니저 테스트"""
    
    @pytest.fixture
    def token_manager(self):
        """보안 토큰 매니저 인스턴스"""
        return SecureTokenManager()
    
    @pytest.fixture
    def sample_user_data(self):
        """테스트용 사용자 데이터"""
        return {
            "user_id": "test_user_123",
            "email": "test@example.com",
            "user_handle": "testuser"
        }
    
    def test_set_secure_cookie(self, token_manager, sample_user_data):
        """보안 쿠키 설정 테스트"""
        app = FastAPI()
        
        @app.post("/test-login")
        async def test_login(response: Response):
            token = "test_jwt_token"
            token_manager.set_secure_cookie(
                response=response,
                token=token,
                cookie_name="access_token"
            )
            return {"message": "login success"}
        
        client = TestClient(app)
        response = client.post("/test-login")
        
        assert response.status_code == 200
        
        # 쿠키 설정 확인
        set_cookie_header = response.headers.get("set-cookie")
        assert set_cookie_header is not None
        
        # HttpOnly 설정 확인
        assert "HttpOnly" in set_cookie_header
        
        # Secure 설정 확인 (HTTPS 환경에서)
        assert "Secure" in set_cookie_header
        
        # SameSite 설정 확인
        assert "SameSite=Strict" in set_cookie_header
    
    def test_extract_token_from_cookie(self, token_manager):
        """쿠키에서 토큰 추출 테스트"""
        app = FastAPI()
        
        @app.get("/test-protected")
        async def test_protected(request):
            token = token_manager.extract_token_from_cookie(
                request=request,
                cookie_name="access_token"
            )
            return {"token": token}
        
        client = TestClient(app)
        
        # 쿠키와 함께 요청
        response = client.get(
            "/test-protected",
            cookies={"access_token": "test_jwt_token"}
        )
        
        assert response.status_code == 200
        assert response.json()["token"] == "test_jwt_token"
    
    def test_clear_secure_cookie(self, token_manager):
        """보안 쿠키 삭제 테스트"""
        app = FastAPI()
        
        @app.post("/test-logout")
        async def test_logout(response: Response):
            token_manager.clear_secure_cookie(
                response=response,
                cookie_name="access_token"
            )
            return {"message": "logout success"}
        
        client = TestClient(app)
        response = client.post("/test-logout")
        
        assert response.status_code == 200
        
        # 쿠키 삭제 확인
        set_cookie_header = response.headers.get("set-cookie")
        assert set_cookie_header is not None
        assert "Max-Age=0" in set_cookie_header or "expires=" in set_cookie_header
    
    def test_token_rotation(self, token_manager, sample_user_data):
        """토큰 로테이션 테스트"""
        old_token = "old_jwt_token"
        new_token = "new_jwt_token"
        
        app = FastAPI()
        
        @app.post("/test-refresh")
        async def test_refresh(response: Response):
            # 새 토큰 설정과 동시에 이전 토큰 무효화
            token_manager.rotate_token(
                response=response,
                old_token=old_token,
                new_token=new_token
            )
            return {"message": "token refreshed"}
        
        client = TestClient(app)
        response = client.post("/test-refresh")
        
        assert response.status_code == 200
        
        # 새 쿠키가 설정되었는지 확인
        set_cookie_header = response.headers.get("set-cookie")
        assert set_cookie_header is not None


class TestAuthServiceSecureCookies:
    """인증 서비스의 보안 쿠키 구현 테스트"""
    
    @pytest.fixture
    def auth_service(self):
        """인증 서비스 인스턴스"""
        return AuthService()
    
    def test_login_with_secure_cookies(self, auth_service):
        """보안 쿠키를 사용한 로그인 테스트"""
        app = FastAPI()
        
        @app.post("/login")
        async def login(response: Response):
            # 실제 사용자 인증 로직은 생략하고 토큰 생성만 테스트
            user_data = {
                "user_id": "test_user",
                "email": "test@example.com"
            }
            
            return await auth_service.login_with_secure_cookies(
                response=response,
                user_data=user_data
            )
        
        client = TestClient(app)
        response = client.post("/login")
        
        assert response.status_code == 200
        
        # 응답에 토큰이 포함되지 않아야 함 (쿠키에만 저장)
        response_data = response.json()
        assert "access_token" not in response_data
        assert "refresh_token" not in response_data
        
        # 쿠키 설정 확인
        cookies = response.cookies
        assert "access_token" in cookies
        assert "refresh_token" in cookies
    
    def test_token_validation_from_cookie(self, auth_service):
        """쿠키에서 토큰 검증 테스트"""
        app = FastAPI()
        
        @app.get("/protected")
        async def protected_route(request):
            # 쿠키에서 토큰 추출 및 검증
            user_data = await auth_service.verify_token_from_cookie(request)
            return {"user": user_data}
        
        # 유효한 토큰으로 테스트
        with patch.object(auth_service, 'verify_access_token') as mock_verify:
            mock_verify.return_value = {
                "user_id": "test_user",
                "email": "test@example.com"
            }
            
            client = TestClient(app)
            response = client.get(
                "/protected",
                cookies={"access_token": "valid_jwt_token"}
            )
            
            assert response.status_code == 200
            assert response.json()["user"]["user_id"] == "test_user"
    
    def test_csrf_protection_with_cookies(self, auth_service):
        """쿠키 기반 인증에서 CSRF 보호 테스트"""
        app = FastAPI()
        
        @app.post("/sensitive-action")
        async def sensitive_action(request):
            # CSRF 토큰 검증
            csrf_valid = await auth_service.verify_csrf_token(request)
            if not csrf_valid:
                return {"error": "CSRF token validation failed"}, 403
            
            return {"message": "action completed"}
        
        client = TestClient(app)
        
        # CSRF 토큰 없이 요청 (실패해야 함)
        response = client.post(
            "/sensitive-action",
            cookies={"access_token": "valid_jwt_token"}
        )
        
        # CSRF 보호로 인해 실패해야 함
        assert response.status_code == 403


class TestTokenStorageComparison:
    """토큰 저장 방식 비교 테스트"""
    
    def test_localStorage_vs_httponly_cookies(self):
        """localStorage vs HttpOnly 쿠키 보안성 비교"""
        
        # localStorage 방식의 취약점 시뮬레이션
        def simulate_xss_attack_localStorage():
            """XSS 공격으로 localStorage에서 토큰 탈취 시뮬레이션"""
            # JavaScript: localStorage.getItem('access_token')
            # 이는 XSS 공격에 취약함
            return "token_stolen_from_localStorage"
        
        # HttpOnly 쿠키 방식의 보안성
        def simulate_xss_attack_httponly():
            """XSS 공격으로 HttpOnly 쿠키 접근 시도 시뮬레이션"""
            # JavaScript에서 HttpOnly 쿠키에 접근할 수 없음
            try:
                # document.cookie로 HttpOnly 쿠키 접근 불가
                return None  # 접근 불가
            except:
                return None
        
        # localStorage는 XSS에 취약
        stolen_token = simulate_xss_attack_localStorage()
        assert stolen_token == "token_stolen_from_localStorage"
        
        # HttpOnly 쿠키는 XSS로부터 보호됨
        protected_token = simulate_xss_attack_httponly()
        assert protected_token is None
    
    def test_secure_cookie_attributes(self):
        """보안 쿠키 속성 테스트"""
        app = FastAPI()
        
        @app.post("/set-secure-token")
        async def set_secure_token(response: Response):
            response.set_cookie(
                key="access_token",
                value="jwt_token",
                httponly=True,      # XSS 방지
                secure=True,        # HTTPS 전용
                samesite="strict",  # CSRF 방지
                max_age=1800,       # 30분 만료
                path="/",           # 전체 경로에서 사용
                domain=None         # 현재 도메인만
            )
            return {"message": "secure token set"}
        
        client = TestClient(app)
        response = client.post("/set-secure-token")
        
        set_cookie_header = response.headers.get("set-cookie")
        
        # 모든 보안 속성이 포함되어야 함
        assert "HttpOnly" in set_cookie_header
        assert "Secure" in set_cookie_header
        assert "SameSite=strict" in set_cookie_header
        assert "Max-Age=1800" in set_cookie_header
        assert "Path=/" in set_cookie_header


class TestTokenSecurityBestPractices:
    """토큰 보안 모범 사례 테스트"""
    
    def test_token_expiration(self):
        """토큰 만료 시간 설정 테스트"""
        from nadle_backend.utils.token_security import TokenExpirationManager
        
        manager = TokenExpirationManager()
        
        # Access Token: 짧은 만료 시간 (15-30분)
        access_token_expiry = manager.get_access_token_expiry()
        assert access_token_expiry <= timedelta(minutes=30)
        
        # Refresh Token: 긴 만료 시간 (7-30일)
        refresh_token_expiry = manager.get_refresh_token_expiry()
        assert refresh_token_expiry >= timedelta(days=7)
        assert refresh_token_expiry <= timedelta(days=30)
    
    def test_token_blacklisting(self):
        """토큰 블랙리스트 기능 테스트"""
        from nadle_backend.utils.token_security import TokenBlacklistManager
        
        manager = TokenBlacklistManager()
        
        # 토큰 무효화
        token = "jwt_token_to_blacklist"
        manager.blacklist_token(token)
        
        # 블랙리스트된 토큰 검증
        assert manager.is_token_blacklisted(token) is True
        
        # 정상 토큰 검증
        valid_token = "valid_jwt_token"
        assert manager.is_token_blacklisted(valid_token) is False
    
    def test_secure_token_transmission(self):
        """토큰 전송 보안 테스트"""
        app = FastAPI()
        
        @app.get("/api/data")
        async def get_data(request):
            # Authorization 헤더보다 쿠키 우선 사용
            token = None
            
            # 1순위: HttpOnly 쿠키
            if "access_token" in request.cookies:
                token = request.cookies["access_token"]
            # 2순위: Authorization 헤더 (API 클라이언트용)
            elif "authorization" in request.headers:
                auth_header = request.headers["authorization"]
                if auth_header.startswith("Bearer "):
                    token = auth_header[7:]
            
            if not token:
                return {"error": "No token provided"}, 401
            
            return {"data": "protected data", "token_source": "cookie" if "access_token" in request.cookies else "header"}
        
        client = TestClient(app)
        
        # 쿠키 기반 요청 (더 안전)
        response = client.get("/api/data", cookies={"access_token": "jwt_token"})
        assert response.status_code == 200
        assert response.json()["token_source"] == "cookie"
        
        # 헤더 기반 요청 (API 클라이언트용)
        response = client.get("/api/data", headers={"Authorization": "Bearer jwt_token"})
        assert response.status_code == 200
        assert response.json()["token_source"] == "header"