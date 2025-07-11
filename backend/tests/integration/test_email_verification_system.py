"""
실제 이메일 발송 시스템 통합 테스트
EmailVerificationService의 전체 플로우를 실제 데이터베이스 및 SMTP와 함께 테스트
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from nadle_backend.config import settings
from nadle_backend.models.email_verification import EmailVerification
from nadle_backend.services.email_verification_service import EmailVerificationService
from nadle_backend.repositories.email_verification_repository import EmailVerificationRepository
from nadle_backend.models.email_verification import EmailVerificationCreate, EmailVerificationCodeRequest


@pytest.fixture(scope="function")
async def test_db():
    """테스트용 데이터베이스 설정"""
    # 테스트용 MongoDB 연결
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client["xai_community_test_email_verification"]
    
    # Beanie 초기화
    await init_beanie(
        database=db,
        document_models=[EmailVerification]
    )
    
    yield db
    
    # 테스트 후 정리
    await client.drop_database("xai_community_test_email_verification")
    client.close()


@pytest.fixture
async def email_verification_service(test_db):
    """실제 데이터베이스를 사용하는 EmailVerificationService"""
    repository = EmailVerificationRepository()
    return EmailVerificationService(repository)


@pytest.fixture
async def clean_test_data():
    """각 테스트 전후 데이터 정리"""
    # 테스트 전 정리
    await EmailVerification.delete_all()
    yield
    # 테스트 후 정리
    await EmailVerification.delete_all()


class TestEmailVerificationSystemIntegration:
    """실제 이메일 발송 시스템 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_complete_email_verification_flow_with_mock_smtp(
        self, 
        email_verification_service: EmailVerificationService,
        clean_test_data
    ):
        """완전한 이메일 인증 플로우 테스트 (Mock SMTP 사용)"""
        test_email = "test@example.com"
        
        # SMTP 발송을 Mock으로 처리
        with patch.object(email_verification_service, '_send_email_smtp', return_value=True) as mock_smtp:
            
            # 1단계: 인증 이메일 발송
            create_request = EmailVerificationCreate(email=test_email)
            send_result = await email_verification_service.send_verification_email(create_request)
            
            # 발송 결과 검증
            assert send_result.code_sent is True
            assert send_result.email == test_email
            assert send_result.expires_in_minutes > 0
            
            # SMTP 발송이 호출되었는지 확인
            mock_smtp.assert_called_once()
            
            # 데이터베이스에 인증 데이터가 저장되었는지 확인
            verification = await EmailVerification.find_one(
                EmailVerification.email == test_email
            )
            assert verification is not None
            assert verification.email == test_email
            assert len(verification.code) == settings.email_verification_code_length
            assert verification.expires_at > datetime.utcnow()
            
            # 2단계: 인증 코드 검증
            verify_request = EmailVerificationCodeRequest(
                email=test_email,
                code=verification.code
            )
            verify_result = await email_verification_service.verify_email_code(verify_request)
            
            # 검증 결과 확인
            assert verify_result.verified is True
            assert verify_result.email == test_email
            assert verify_result.can_proceed is True
            
            # 인증 데이터가 검증되었는지 확인
            used_verification = await EmailVerification.get(verification.id)
            assert used_verification.is_verified is True
    
    @pytest.mark.asyncio
    async def test_multiple_email_verification_requests(
        self, 
        email_verification_service: EmailVerificationService,
        clean_test_data
    ):
        """동일 이메일로 여러 번 인증 요청시 처리 테스트"""
        test_email = "test@example.com"
        
        with patch.object(email_verification_service, '_send_email_smtp', return_value=True):
            
            # 첫 번째 인증 요청
            create_request = EmailVerificationCreate(email=test_email)
            first_result = await email_verification_service.send_verification_email(create_request)
            assert first_result.code_sent is True
            
            # 첫 번째 인증 데이터 확인
            first_verification = await EmailVerification.find_one(
                EmailVerification.email == test_email
            )
            first_code = first_verification.code
            
            # 두 번째 인증 요청 - 기존 코드가 만료되지 않으면 재전송하지 않음
            second_result = await email_verification_service.send_verification_email(create_request)
            
            # 기존 코드가 아직 유효하므로 재전송하지 않음
            if not first_verification.is_expired():
                assert second_result.code_sent is False
                assert "이미 전송된 인증 코드가 있습니다" in second_result.message
                
                # 기존 코드로 인증 시도하면 성공해야 함
                verify_request = EmailVerificationCodeRequest(
                    email=test_email,
                    code=first_code
                )
                verify_result = await email_verification_service.verify_email_code(verify_request)
                assert verify_result.verified is True
                return
            
            # 만약 만료되었다면 새로운 코드 생성
            assert second_result.code_sent is True
            
            # 새로운 인증 데이터 확인 (최신 것을 가져옴)
            second_verification = await EmailVerification.find_one(
                EmailVerification.email == test_email
            )
            assert second_verification is not None
            
            # 새로운 코드가 생성되었는지 확인
            assert second_verification.code != first_code
            
            # 첫 번째 코드로는 인증 실패해야 함
            verify_old_request = EmailVerificationCodeRequest(
                email=test_email,
                code=first_code
            )
            verify_old_result = await email_verification_service.verify_email_code(verify_old_request)
            assert verify_old_result.verified is False
            
            # 새로운 코드로는 인증 성공해야 함
            verify_new_request = EmailVerificationCodeRequest(
                email=test_email,
                code=second_verification.code
            )
            verify_new_result = await email_verification_service.verify_email_code(verify_new_request)
            assert verify_new_result.verified is True
    
    @pytest.mark.asyncio
    async def test_expired_verification_code(
        self, 
        email_verification_service: EmailVerificationService,
        clean_test_data
    ):
        """만료된 인증 코드 처리 테스트"""
        test_email = "test@example.com"
        
        with patch.object(email_verification_service, '_send_email_smtp', return_value=True):
            
            # 인증 이메일 발송
            create_request = EmailVerificationCreate(email=test_email)
            await email_verification_service.send_verification_email(create_request)
            
            # 저장된 인증 데이터 가져오기
            verification = await EmailVerification.find_one(
                EmailVerification.email == test_email
            )
            
            # 강제로 만료 시간을 과거로 설정
            verification.expires_at = datetime.utcnow() - timedelta(minutes=1)
            await verification.save()
            
            # 만료된 코드로 인증 시도
            verify_request = EmailVerificationCodeRequest(
                email=test_email,
                code=verification.code
            )
            verify_result = await email_verification_service.verify_email_code(verify_request)
            
            # 만료로 인한 실패 확인
            assert verify_result.verified is False
            assert "만료" in verify_result.message
    
    @pytest.mark.asyncio
    async def test_wrong_verification_code_attempts(
        self, 
        email_verification_service: EmailVerificationService,
        clean_test_data
    ):
        """잘못된 인증 코드 시도 횟수 제한 테스트"""
        test_email = "test@example.com"
        
        with patch.object(email_verification_service, '_send_email_smtp', return_value=True):
            
            # 인증 이메일 발송
            create_request = EmailVerificationCreate(email=test_email)
            await email_verification_service.send_verification_email(create_request)
            
            # 저장된 인증 데이터 가져오기
            verification = await EmailVerification.find_one(
                EmailVerification.email == test_email
            )
            correct_code = verification.code
            
            # 최대 시도 횟수만큼 잘못된 코드로 시도
            for attempt in range(settings.email_verification_max_attempts):
                wrong_request = EmailVerificationCodeRequest(
                    email=test_email,
                    code="000000"  # 잘못된 코드
                )
                result = await email_verification_service.verify_email_code(wrong_request)
                assert result.verified is False
            
            # 최대 시도 횟수 초과 후 올바른 코드로도 인증 불가능해야 함
            correct_request = EmailVerificationCodeRequest(
                email=test_email,
                code=correct_code
            )
            blocked_result = await email_verification_service.verify_email_code(correct_request)
            assert blocked_result.verified is False
            assert "최대 시도 횟수" in blocked_result.message or "차단" in blocked_result.message
    
    @pytest.mark.asyncio
    async def test_email_content_generation(
        self, 
        email_verification_service: EmailVerificationService
    ):
        """이메일 콘텐츠 생성 테스트"""
        test_email = "test@example.com"
        test_code = "123456"
        
        # 이메일 콘텐츠 생성
        subject, html_content = email_verification_service._create_email_content(test_code, test_email)
        
        # 제목 검증
        assert "이메일 인증" in subject
        assert "XAI Community" in subject or settings.from_name in subject
        
        # HTML 콘텐츠 검증
        assert test_code in html_content
        assert settings.from_name in html_content
        assert "시간 후에 만료됩니다" in html_content or "분 후" in html_content
        assert "인증 코드" in html_content
        assert "주의사항" in html_content
        
        # HTML 구조 확인
        assert "<html>" in html_content
        assert "</html>" in html_content
        assert "<body" in html_content  # style 속성이 있을 수 있으므로
        assert "</body>" in html_content
    
    @pytest.mark.asyncio
    async def test_smtp_failure_handling(
        self, 
        email_verification_service: EmailVerificationService,
        clean_test_data
    ):
        """SMTP 발송 실패 처리 테스트"""
        test_email = "test@example.com"
        
        # SMTP 발송 실패 시뮬레이션
        with patch.object(email_verification_service, '_send_email_smtp', return_value=False):
            
            create_request = EmailVerificationCreate(email=test_email)
            result = await email_verification_service.send_verification_email(create_request)
            
            # 발송 실패 처리 확인
            assert result.code_sent is False
            assert "이메일 전송에 실패했습니다" in result.message
            
            # SMTP 실패시에도 데이터베이스에는 저장되어 있을 수 있음 (실제 구현에 따라)
            # 대신 이메일 전송 실패 응답이 올바른지만 확인
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_verifications(
        self, 
        email_verification_service: EmailVerificationService,
        clean_test_data
    ):
        """만료된 인증 데이터 정리 테스트"""
        # 만료된 인증 데이터 직접 생성
        expired_verification = EmailVerification(
            email="expired@example.com",
            code="123456",
            expires_at=datetime.utcnow() - timedelta(hours=1),
            attempt_count=0
        )
        await expired_verification.insert()
        
        # 정리 메서드 호출
        cleaned_count = await email_verification_service.cleanup_expired_verifications()
        
        # 정리 결과 확인
        assert cleaned_count >= 1
        
        # 만료된 데이터가 삭제되었는지 확인
        remaining = await EmailVerification.find_one(
            EmailVerification.email == "expired@example.com"
        )
        assert remaining is None


@pytest.mark.integration
class TestRealEmailVerificationSystem:
    """실제 SMTP를 사용한 시스템 테스트 (수동 활성화용)"""
    
    @pytest.mark.skip(reason="Real SMTP system test - enable manually for full integration testing")
    @pytest.mark.asyncio
    async def test_complete_real_email_verification_flow(
        self, 
        email_verification_service: EmailVerificationService,
        clean_test_data
    ):
        """실제 Gmail SMTP를 사용한 완전한 이메일 인증 플로우 테스트
        
        주의: 이 테스트는 실제 이메일을 발송합니다.
        수동으로 활성화하여 실행하세요.
        """
        # 자신의 이메일로 테스트 (실제 이메일 수신)
        test_email = settings.smtp_username
        
        print(f"실제 이메일 인증 테스트 시작: {test_email}")
        
        # 1단계: 실제 인증 이메일 발송
        create_request = EmailVerificationCreate(email=test_email)
        send_result = await email_verification_service.send_verification_email(create_request)
        
        assert send_result.code_sent is True
        print(f"인증 이메일 발송 성공: {send_result.message}")
        
        # 저장된 인증 코드 가져오기 (실제 환경에서는 사용자가 이메일에서 확인)
        verification = await EmailVerification.find_one(
            EmailVerification.email == test_email
        )
        assert verification is not None
        
        print(f"생성된 인증 코드: {verification.code}")
        print("실제 이메일을 확인하여 동일한 코드가 발송되었는지 확인하세요.")
        
        # 2단계: 인증 코드 검증
        verify_request = EmailVerificationCodeRequest(
            email=test_email,
            code=verification.code
        )
        verify_result = await email_verification_service.verify_email_code(verify_request)
        
        assert verify_result.verified is True
        print(f"인증 코드 검증 성공: {verify_result.message}")
        
        print("✅ 실제 이메일 인증 플로우 테스트 완료")