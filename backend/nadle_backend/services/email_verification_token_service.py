"""
작업 시간: 2025-07-25 09:22:00 KST
작업 버전: v1.0.0
주요 컴포넌트들: EmailVerificationTokenService
주요 함수들:
- send_verification_token_email: 토큰 기반 인증 이메일 전송 (L35-65)
- verify_token: 토큰 검증 및 인증 완료 처리 (L67-85)
- check_verification_status: 이메일 인증 상태 확인 (L87-100)
- create_verification_email_with_button: 버튼 포함 이메일 템플릿 생성 (L102-150)
- _send_email: SMTP 이메일 전송 (L152-180)
관련 파일들:
- repositories/email_verification_token_repository.py: 데이터 액세스
- models/email_verification.py: 데이터 모델
- config.py: 설정 정보
"""

import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Tuple

from ..config import settings
from ..models.email_verification import (
    EmailVerificationToken,
    EmailVerificationTokenRequest,
    EmailVerificationTokenResponse,
    EmailVerificationStatusResponse,
)
from ..repositories.email_verification_token_repository import EmailVerificationTokenRepository

logger = logging.getLogger(__name__)


class EmailVerificationTokenService:
    """Service for handling token-based email verification during signup."""

    def __init__(self, repository: EmailVerificationTokenRepository):
        self.repository = repository

    async def send_verification_token_email(
        self, request: EmailVerificationTokenRequest, client_ip: str = None
    ) -> EmailVerificationTokenResponse:
        """Send verification email with token link to user."""
        email = "unknown"  # 기본값 설정
        try:
            logger.info(f"🚀 Starting email verification token process for request: {request}")
            
            try:
                logger.info(f"📧 Request object: {request}")
                logger.info(f"📧 Request type: {type(request)}")
                logger.info(f"📧 Request attributes: {dir(request)}")
                
                if hasattr(request, 'email'):
                    logger.info(f"📧 request.email exists: {request.email}")
                    email = request.email.lower()
                    logger.info(f"📧 Processing email: {email}")
                else:
                    logger.error(f"❌ request object has no email attribute!")
                    raise AttributeError("request object missing email attribute")
                    
            except Exception as e:
                logger.error(f"❌ Error processing email from request: {e}")
                raise e

            # Create token verification
            try:
                logger.info(f"🔑 Creating token verification...")
                verification = await self.repository.create_token_verification(
                    email=email,
                    expire_minutes=settings.email_verification_token_expire_minutes,
                    created_ip=client_ip
                )
                logger.info(f"✅ Token created: {verification.token[:10]}... for {verification.email}")
            except Exception as e:
                logger.error(f"❌ Error creating token verification: {e}")
                raise e

            # Create verification link (backend endpoint that redirects to frontend)
            try:
                backend_base_url = settings.backend_url or "http://localhost:8000"
                verification_link = f"{backend_base_url}/api/auth/verify-email-token/{verification.token}"
                logger.info(f"🔗 Verification link created: {verification_link}")
            except Exception as e:
                logger.error(f"❌ Error creating verification link: {e}")
                raise e

            # Create email content
            try:
                logger.info(f"📝 Creating email content...")
                subject, html_content = self.create_verification_email_with_button(
                    verification_link, email
                )
                logger.info(f"📄 Email content created. Subject: {subject}")
            except Exception as e:
                logger.error(f"❌ Error creating email content: {e}")
                raise e

            # Send email
            try:
                logger.info(f"📤 Attempting to send email to {email}...")
                success = await self._send_email(email, subject, html_content)
                logger.info(f"📬 Email send result: {success}")
            except Exception as e:
                logger.error(f"❌ Error sending email: {e}")
                raise e

            if success:
                logger.info(f"Verification token email sent successfully to {email}")
                return EmailVerificationTokenResponse(
                    success=True,
                    email=email,
                    token_sent=True,
                    expires_in_minutes=verification.time_until_expiry(),
                    message="인증 이메일이 전송되었습니다. 이메일을 확인해주세요."
                )
            else:
                return EmailVerificationTokenResponse(
                    success=False,
                    email=email,
                    token_sent=False,
                    expires_in_minutes=0,
                    message="이메일 전송에 실패했습니다."
                )

        except Exception as e:
            # email 변수가 정의되지 않은 경우를 처리
            email_value = request.email.lower() if hasattr(request, 'email') else "unknown"
            error_info = f"{type(e).__name__}: {str(e)}"
            logger.error(f"Failed to send verification token email to {email_value}: {error_info}")
            
            # 개발환경에서는 더 자세한 오류 정보 제공
            import traceback
            trace_info = traceback.format_exc()
            logger.error(f"Detailed traceback: {trace_info}")
            
            return EmailVerificationTokenResponse(
                success=False,
                email=email_value,
                token_sent=False,
                expires_in_minutes=0,
                message=f"이메일 전송 실패: {error_info}"
            )

    async def verify_token(self, token: str) -> Tuple[bool, str]:
        """Verify email verification token."""
        try:
            verification = await self.repository.get_by_token(token)
            
            if not verification:
                return False, "유효하지 않은 인증 토큰입니다."
            
            if verification.is_expired():
                return False, "인증 토큰이 만료되었습니다."
            
            if verification.is_verified:
                return True, "이미 인증이 완료되었습니다."
            
            # Mark as verified
            success = await self.repository.mark_as_verified(token)
            if success:
                logger.info(f"Email token verification completed for {verification.email}")
                return True, "이메일 인증이 완료되었습니다."
            else:
                return False, "인증 처리 중 오류가 발생했습니다."

        except Exception as e:
            logger.error(f"Failed to verify token {token}: {str(e)}")
            return False, f"인증 확인 중 오류가 발생했습니다: {str(e)}"

    async def check_verification_status(self, email: str) -> EmailVerificationStatusResponse:
        """Check email verification status."""
        try:
            verification = await self.repository.get_by_email(email.lower())
            
            if not verification:
                return EmailVerificationStatusResponse(
                    email=email,
                    is_verified=False,
                    message="인증 요청이 없습니다."
                )
            
            if verification.is_expired():
                return EmailVerificationStatusResponse(
                    email=email,
                    is_verified=False,
                    message="인증 토큰이 만료되었습니다."
                )
            
            return EmailVerificationStatusResponse(
                email=email,
                is_verified=verification.is_verified,
                message="인증 완료" if verification.is_verified else "인증 대기 중"
            )

        except Exception as e:
            logger.error(f"Failed to check verification status for {email}: {str(e)}")
            return EmailVerificationStatusResponse(
                email=email,
                is_verified=False,
                message="상태 확인 중 오류가 발생했습니다."
            )

    def create_verification_email_with_button(
        self, verification_link: str, email: str
    ) -> Tuple[str, str]:
        """Create email content with verification button."""
        subject = f"{settings.from_name} - 이메일 인증"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 40px;">
                <h1 style="color: #333; margin-bottom: 10px;">{settings.from_name}</h1>
                <p style="color: #666; margin: 0;">이메일 인증을 완료해주세요</p>
            </div>
            
            <div style="background-color: #f8f9fa; padding: 30px; border-radius: 10px; text-align: center;">
                <h2 style="color: #333; margin-bottom: 20px;">회원가입을 완료하려면</h2>
                <p style="color: #666; margin-bottom: 30px; font-size: 16px;">
                    아래 버튼을 클릭하여 이메일 인증을 완료해주세요.
                </p>
                
                <a href="{verification_link}" 
                   style="display: inline-block; background-color: #007bff; color: white; 
                          padding: 15px 30px; text-decoration: none; border-radius: 8px; 
                          font-weight: bold; font-size: 16px; margin: 20px 0;">
                    이메일 인증하기
                </a>
                
                <p style="color: #666; margin-top: 30px; font-size: 14px;">
                    이 링크는 {settings.email_verification_token_expire_minutes}분 후에 만료됩니다.
                </p>
                
                <div style="margin-top: 20px; padding: 15px; background-color: #e9ecef; border-radius: 5px;">
                    <p style="color: #666; margin: 0; font-size: 12px;">
                        버튼이 작동하지 않는 경우 아래 링크를 복사하여 브라우저에 붙여넣으세요:<br>
                        <span style="word-break: break-all; color: #007bff;">{verification_link}</span>
                    </p>
                </div>
            </div>
            
            <div style="margin-top: 30px; padding: 20px; background-color: #fff3cd; border-radius: 8px;">
                <h3 style="color: #856404; margin-top: 0;">주의사항</h3>
                <ul style="color: #856404; margin: 0; padding-left: 20px;">
                    <li>이 이메일은 자동으로 발송된 메일입니다.</li>
                    <li>인증 링크를 다른 사람과 공유하지 마세요.</li>
                    <li>만약 이 요청을 하지 않았다면 이 이메일을 무시하세요.</li>
                </ul>
            </div>
            
            <div style="text-align: center; margin-top: 30px; color: #666; font-size: 12px;">
                <p>© 2024 {settings.from_name}. All rights reserved.</p>
            </div>
        </body>
        </html>
        """

        return subject, html_content

    async def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email using SMTP."""
        try:
            # Check settings first
            logger.info(f"🔧 Email Settings Check:")
            logger.info(f"  - email_mock_mode: {settings.email_mock_mode}")
            logger.info(f"  - smtp_server: {settings.smtp_server}")
            logger.info(f"  - smtp_port: {settings.smtp_port}")
            logger.info(f"  - smtp_username: {settings.smtp_username}")
            logger.info(f"  - smtp_password: {'***' if settings.smtp_password else 'NOT SET'}")
            logger.info(f"  - from_email: {settings.from_email}")
            logger.info(f"  - from_name: {settings.from_name}")
            
            # Mock mode for development
            if settings.email_mock_mode:
                logger.info(f"📧 MOCK MODE: Email would be sent to {to_email}")
                logger.info(f"📧 MOCK MODE: Subject: {subject}")
                logger.info(f"📧 MOCK MODE: Verification link in content (simulated)")
                return True
                
            logger.info(f"🔧 SMTP Settings - Server: {settings.smtp_server}, Port: {settings.smtp_port}")
            logger.info(f"🔧 SMTP Settings - Username: {settings.smtp_username}, TLS: {settings.smtp_use_tls}")
            
            # Create message
            logger.info(f"📨 Creating email message...")
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.from_name} <{settings.from_email}>"
            msg["To"] = to_email
            logger.info(f"📨 Message headers set. From: {msg['From']}, To: {msg['To']}")

            # Attach HTML content
            html_part = MIMEText(html_content, "html", "utf-8")
            msg.attach(html_part)
            logger.info(f"📨 HTML content attached")

            # Send email
            logger.info(f"🌐 Connecting to SMTP server {settings.smtp_server}:{settings.smtp_port}...")
            with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
                logger.info(f"✅ SMTP connection established")
                
                if settings.smtp_use_tls:
                    logger.info(f"🔒 Starting TLS...")
                    server.starttls()
                    logger.info(f"🔒 TLS started successfully")
                
                logger.info(f"🔑 Logging in with username: {settings.smtp_username}")
                server.login(settings.smtp_username, settings.smtp_password)
                logger.info(f"🔑 SMTP login successful")
                
                logger.info(f"📤 Sending message...")
                server.send_message(msg)
                logger.info(f"📤 Message sent successfully")

            logger.info(f"✅ Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"📍 Traceback: {traceback.format_exc()}")
            return False