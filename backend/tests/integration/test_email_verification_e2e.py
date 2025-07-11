"""
E2E (End-to-End) 테스트 - 이메일 인증 전체 플로우
API 엔드포인트부터 데이터베이스까지 전체 스택을 통한 테스트
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from httpx import AsyncClient
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from unittest.mock import patch, MagicMock

from nadle_backend.config import settings
from nadle_backend.models.email_verification import EmailVerification
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from main import app


@pytest.fixture(scope="function")
async def test_db():
    """테스트용 데이터베이스 설정"""
    # 테스트용 MongoDB 연결
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client["xai_community_test_e2e_email_verification"]
    
    # Beanie 초기화
    await init_beanie(
        database=db,
        document_models=[EmailVerification]
    )
    
    yield db
    
    # 테스트 후 정리
    await client.drop_database("xai_community_test_e2e_email_verification")
    client.close()


@pytest.fixture
async def clean_test_data():
    """각 테스트 전후 데이터 정리"""
    # 테스트 전 정리
    await EmailVerification.delete_all()
    yield
    # 테스트 후 정리
    await EmailVerification.delete_all()


@pytest.fixture
async def test_client():
    """테스트용 HTTP 클라이언트"""
    from fastapi.testclient import TestClient
    # 비동기 테스트를 위한 동기 클라이언트 (FastAPI가 내부적으로 비동기 처리)
    with TestClient(app) as client:
        yield client


class TestEmailVerificationE2E:
    """이메일 인증 E2E 테스트"""
    
    @pytest.mark.asyncio
    async def test_complete_email_verification_flow_via_api(
        self,
        test_client: AsyncClient,
        test_db,
        clean_test_data
    ):
        """API를 통한 완전한 이메일 인증 플로우 E2E 테스트"""
        test_email = "e2e_test@example.com"
        
        # SMTP 발송을 Mock으로 처리
        with patch('nadle_backend.services.email_verification_service.EmailVerificationService._send_email_smtp', return_value=True) as mock_smtp:
            
            # 1단계: API를 통한 인증 이메일 발송
            send_response = await test_client.post(
                "/api/auth/send-verification-email",
                json={"email": test_email}
            )
            
            # API 응답 검증
            assert send_response.status_code == 200
            send_data = send_response.json()
            assert send_data["email"] == test_email
            assert send_data["code_sent"] is True
            assert send_data["expires_in_minutes"] > 0
            assert "전송되었습니다" in send_data["message"]
            
            # SMTP 발송이 호출되었는지 확인
            mock_smtp.assert_called_once()
            
            # 데이터베이스에서 인증 데이터 확인
            verification = await EmailVerification.find_one(
                EmailVerification.email == test_email
            )
            assert verification is not None
            assert verification.email == test_email
            assert len(verification.code) == 6
            assert verification.expires_at > datetime.utcnow()
            
            # 2단계: API를 통한 인증 코드 검증
            verify_response = await test_client.post(
                "/api/auth/verify-email-code",
                json={
                    "email": test_email,
                    "code": verification.code
                }
            )
            
            # API 응답 검증
            assert verify_response.status_code == 200
            verify_data = verify_response.json()
            assert verify_data["email"] == test_email
            assert verify_data["verified"] is True
            assert verify_data["can_proceed"] is True
            assert "완료되었습니다" in verify_data["message"]
            
            # 데이터베이스에서 검증 상태 확인
            updated_verification = await EmailVerification.get(verification.id)
            assert updated_verification.is_verified is True
    
    @pytest.mark.asyncio
    async def test_wrong_email_verification_code_via_api(
        self,
        test_client: AsyncClient,
        test_db,
        clean_test_data
    ):
        """잘못된 인증 코드 API 테스트"""
        test_email = "wrong_code_test@example.com"
        
        with patch('nadle_backend.services.email_verification_service.EmailVerificationService._send_email_smtp', return_value=True):
            
            # 인증 이메일 발송
            send_response = await test_client.post(
                "/api/auth/send-verification-email",
                json={"email": test_email}
            )
            assert send_response.status_code == 200
            
            # 잘못된 코드로 인증 시도
            verify_response = await test_client.post(
                "/api/auth/verify-email-code",
                json={
                    "email": test_email,
                    "code": "000000"  # 잘못된 코드
                }
            )
            
            # API 응답 검증
            assert verify_response.status_code == 200
            verify_data = verify_response.json()
            assert verify_data["email"] == test_email
            assert verify_data["verified"] is False
            assert verify_data["can_proceed"] is False
            assert "잘못된" in verify_data["message"]
    
    @pytest.mark.asyncio
    async def test_expired_verification_code_via_api(
        self,
        test_client: AsyncClient,
        test_db,
        clean_test_data
    ):
        """만료된 인증 코드 API 테스트"""
        test_email = "expired_test@example.com"
        
        with patch('nadle_backend.services.email_verification_service.EmailVerificationService._send_email_smtp', return_value=True):
            
            # 인증 이메일 발송
            send_response = await test_client.post(
                "/api/auth/send-verification-email",
                json={"email": test_email}
            )
            assert send_response.status_code == 200
            
            # 데이터베이스에서 인증 데이터 가져와서 강제로 만료시키기
            verification = await EmailVerification.find_one(
                EmailVerification.email == test_email
            )
            verification.expires_at = datetime.utcnow() - timedelta(minutes=1)
            await verification.save()
            
            # 만료된 코드로 인증 시도
            verify_response = await test_client.post(
                "/api/auth/verify-email-code",
                json={
                    "email": test_email,
                    "code": verification.code
                }
            )
            
            # API 응답 검증
            assert verify_response.status_code == 200
            verify_data = verify_response.json()
            assert verify_data["verified"] is False
            assert "만료" in verify_data["message"]
    
    @pytest.mark.asyncio
    async def test_multiple_verification_attempts_via_api(
        self,
        test_client: AsyncClient,
        test_db,
        clean_test_data
    ):
        """여러 번 인증 시도 API 테스트"""
        test_email = "multiple_attempts_test@example.com"
        
        with patch('nadle_backend.services.email_verification_service.EmailVerificationService._send_email_smtp', return_value=True):
            
            # 인증 이메일 발송
            send_response = await test_client.post(
                "/api/auth/send-verification-email",
                json={"email": test_email}
            )
            assert send_response.status_code == 200
            
            # 최대 시도 횟수만큼 잘못된 코드로 시도
            for attempt in range(settings.email_verification_max_attempts):
                verify_response = await test_client.post(
                    "/api/auth/verify-email-code",
                    json={
                        "email": test_email,
                        "code": "000000"  # 잘못된 코드
                    }
                )
                assert verify_response.status_code == 200
                verify_data = verify_response.json()
                assert verify_data["verified"] is False
            
            # 이제 올바른 코드로도 인증 불가능해야 함
            verification = await EmailVerification.find_one(
                EmailVerification.email == test_email
            )
            
            correct_verify_response = await test_client.post(
                "/api/auth/verify-email-code",
                json={
                    "email": test_email,
                    "code": verification.code
                }
            )
            
            assert correct_verify_response.status_code == 200
            correct_verify_data = correct_verify_response.json()
            assert correct_verify_data["verified"] is False
            assert "최대 시도 횟수" in correct_verify_data["message"] or "차단" in correct_verify_data["message"]
    
    @pytest.mark.asyncio
    async def test_duplicate_email_verification_requests_via_api(
        self,
        test_client: AsyncClient,
        test_db,
        clean_test_data
    ):
        """중복 이메일 인증 요청 API 테스트"""
        test_email = "duplicate_test@example.com"
        
        with patch('nadle_backend.services.email_verification_service.EmailVerificationService._send_email_smtp', return_value=True):
            
            # 첫 번째 인증 이메일 발송
            first_response = await test_client.post(
                "/api/auth/send-verification-email",
                json={"email": test_email}
            )
            assert first_response.status_code == 200
            first_data = first_response.json()
            assert first_data["code_sent"] is True
            
            # 즉시 두 번째 요청 (기존 코드가 아직 유효함)
            second_response = await test_client.post(
                "/api/auth/send-verification-email",
                json={"email": test_email}
            )
            assert second_response.status_code == 200
            second_data = second_response.json()
            assert second_data["code_sent"] is False
            assert "이미 전송된" in second_data["message"]
    
    @pytest.mark.asyncio
    async def test_invalid_email_format_via_api(
        self,
        test_client: AsyncClient,
        test_db,
        clean_test_data
    ):
        """잘못된 이메일 형식 API 테스트"""
        
        # 잘못된 이메일 형식으로 요청
        response = await test_client.post(
            "/api/auth/send-verification-email",
            json={"email": "invalid-email-format"}
        )
        
        # 검증 오류 응답 확인
        assert response.status_code == 422  # Validation Error
        error_data = response.json()
        assert "detail" in error_data
        assert any("email" in str(error).lower() for error in error_data["detail"])
    
    @pytest.mark.asyncio
    async def test_missing_email_field_via_api(
        self,
        test_client: AsyncClient,
        test_db,
        clean_test_data
    ):
        """이메일 필드 누락 API 테스트"""
        
        # 이메일 필드 없이 요청
        response = await test_client.post(
            "/api/auth/send-verification-email",
            json={}
        )
        
        # 검증 오류 응답 확인
        assert response.status_code == 422  # Validation Error
        error_data = response.json()
        assert "detail" in error_data
        assert any("email" in str(error).lower() for error in error_data["detail"])
    
    @pytest.mark.asyncio
    async def test_missing_verification_code_field_via_api(
        self,
        test_client: AsyncClient,
        test_db,
        clean_test_data
    ):
        """인증 코드 필드 누락 API 테스트"""
        
        # 코드 필드 없이 인증 시도
        response = await test_client.post(
            "/api/auth/verify-email-code",
            json={"email": "test@example.com"}
        )
        
        # 검증 오류 응답 확인
        assert response.status_code == 422  # Validation Error
        error_data = response.json()
        assert "detail" in error_data
        assert any("code" in str(error).lower() for error in error_data["detail"])
    
    @pytest.mark.asyncio
    async def test_smtp_failure_via_api(
        self,
        test_client: AsyncClient,
        test_db,
        clean_test_data
    ):
        """SMTP 실패 상황 API 테스트"""
        test_email = "smtp_failure_test@example.com"
        
        # SMTP 발송 실패 시뮬레이션
        with patch('nadle_backend.services.email_verification_service.EmailVerificationService._send_email_smtp', return_value=False):
            
            response = await test_client.post(
                "/api/auth/send-verification-email",
                json={"email": test_email}
            )
            
            # API는 성공적으로 응답하지만 이메일 발송 실패를 알림
            assert response.status_code == 200
            data = response.json()
            assert data["code_sent"] is False
            assert "전송에 실패했습니다" in data["message"]
    
    @pytest.mark.asyncio
    async def test_email_verification_with_special_characters_via_api(
        self,
        test_client: AsyncClient,
        test_db,
        clean_test_data
    ):
        """특수 문자가 포함된 이메일 주소 API 테스트"""
        test_email = "test+special@example.com"
        
        with patch('nadle_backend.services.email_verification_service.EmailVerificationService._send_email_smtp', return_value=True):
            
            # 특수 문자가 포함된 이메일로 인증 요청
            response = await test_client.post(
                "/api/auth/send-verification-email",
                json={"email": test_email}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == test_email
            assert data["code_sent"] is True
            
            # 데이터베이스에서 정규화된 이메일 확인
            verification = await EmailVerification.find_one(
                EmailVerification.email == test_email.lower()
            )
            assert verification is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_verification_requests_via_api(
        self,
        test_client: AsyncClient,
        test_db,
        clean_test_data
    ):
        """동시 인증 요청 API 테스트"""
        test_email = "concurrent_test@example.com"
        
        with patch('nadle_backend.services.email_verification_service.EmailVerificationService._send_email_smtp', return_value=True):
            
            # 동시에 여러 요청 보내기
            tasks = []
            for _ in range(3):
                task = test_client.post(
                    "/api/auth/send-verification-email",
                    json={"email": test_email}
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks)
            
            # 모든 응답이 성공적이어야 함
            for response in responses:
                assert response.status_code == 200
            
            # 첫 번째는 성공, 나머지는 중복 요청으로 처리될 수 있음
            successful_count = sum(1 for resp in responses if resp.json()["code_sent"] is True)
            duplicate_count = sum(1 for resp in responses if resp.json()["code_sent"] is False)
            
            # 최소 하나는 성공해야 함
            assert successful_count >= 1
            # 총합은 요청 수와 같아야 함
            assert successful_count + duplicate_count == 3


@pytest.mark.integration
class TestRealEmailVerificationE2E:
    """실제 SMTP를 사용한 E2E 테스트 (수동 활성화용)"""
    
    @pytest.mark.skip(reason="Real SMTP E2E test - enable manually for full system testing")
    @pytest.mark.asyncio
    async def test_real_email_verification_complete_flow_via_api(
        self,
        test_client: AsyncClient,
        test_db,
        clean_test_data
    ):
        """실제 Gmail SMTP를 사용한 완전한 E2E 테스트
        
        주의: 이 테스트는 실제 이메일을 발송합니다.
        수동으로 활성화하여 실행하세요.
        """
        # 자신의 이메일로 테스트 (실제 이메일 수신)
        test_email = settings.smtp_username
        
        print(f"실제 E2E 이메일 인증 테스트 시작: {test_email}")
        
        # 1단계: 실제 인증 이메일 발송 API 호출
        send_response = await test_client.post(
            "/api/auth/send-verification-email",
            json={"email": test_email}
        )
        
        assert send_response.status_code == 200
        send_data = send_response.json()
        assert send_data["code_sent"] is True
        print(f"인증 이메일 발송 API 성공: {send_data['message']}")
        
        # 데이터베이스에서 실제 인증 코드 가져오기
        verification = await EmailVerification.find_one(
            EmailVerification.email == test_email
        )
        assert verification is not None
        
        print(f"생성된 인증 코드: {verification.code}")
        print("실제 이메일을 확인하여 동일한 코드가 발송되었는지 확인하세요.")
        
        # 2단계: 실제 인증 코드로 검증 API 호출
        verify_response = await test_client.post(
            "/api/auth/verify-email-code",
            json={
                "email": test_email,
                "code": verification.code
            }
        )
        
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        assert verify_data["verified"] is True
        print(f"인증 코드 검증 API 성공: {verify_data['message']}")
        
        print("✅ 실제 E2E 이메일 인증 플로우 테스트 완료")