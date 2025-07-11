"""Service for email verification during signup process."""

import smtplib
import secrets
import string
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Tuple
import logging

from ..config import settings
from ..models.email_verification import (
    EmailVerification,
    EmailVerificationData,
    EmailVerificationCreate,
    EmailVerificationResponse,
    EmailVerificationCodeRequest,
    EmailVerificationCodeResponse
)
from ..repositories.email_verification_repository import EmailVerificationRepository

logger = logging.getLogger(__name__)


class EmailVerificationService:
    """Service for handling email verification during signup."""
    
    def __init__(self, repository: EmailVerificationRepository):
        self.repository = repository
    
    async def send_verification_email(self, request: EmailVerificationCreate) -> EmailVerificationResponse:
        """Send verification email to user."""
        try:
            email = request.email.lower()
            
            # Check if there's an existing verification
            existing = await self.repository.get_by_email(email)
            
            if existing and not existing.is_expired():
                # Still valid verification exists
                return EmailVerificationResponse(
                    success=False,
                    email=email,
                    code_sent=False,
                    expires_in_minutes=existing.time_until_expiry(),
                    can_resend=False,
                    message="이미 전송된 인증 코드가 있습니다. 만료 후 다시 요청해주세요."
                )
            
            # Generate new verification code
            code = self._generate_verification_code()
            
            # Create new verification
            verification = EmailVerification.create_verification(
                email=email,
                code=code,
                expire_minutes=getattr(settings, 'email_verification_expire_minutes', 5)
            )
            
            # Save to database
            await self.repository.create(verification)
            
            # Send email
            success = await self._send_email_smtp(
                to_email=email,
                subject=f"{settings.from_name} - 이메일 인증",
                html_content=self._create_email_content(code, email)[1]
            )
            
            if success:
                logger.info(f"Verification email sent successfully to {email}")
                return EmailVerificationResponse(
                    success=True,
                    email=email,
                    code_sent=True,
                    expires_in_minutes=verification.time_until_expiry(),
                    can_resend=False,
                    message="인증 코드가 이메일로 전송되었습니다."
                )
            else:
                return EmailVerificationResponse(
                    success=False,
                    email=email,
                    code_sent=False,
                    expires_in_minutes=0,
                    can_resend=True,
                    message="이메일 전송에 실패했습니다. 다시 시도해주세요."
                )
                
        except Exception as e:
            logger.error(f"Failed to send verification email to {request.email}: {str(e)}")
            return EmailVerificationResponse(
                success=False,
                email=request.email,
                code_sent=False,
                expires_in_minutes=0,
                can_resend=True,
                message=f"이메일 전송 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def verify_email_code(self, request: EmailVerificationCodeRequest) -> EmailVerificationCodeResponse:
        """Verify email verification code."""
        try:
            email = request.email.lower()
            code = request.code
            
            # Get verification record
            verification = await self.repository.get_by_email(email)
            
            if not verification:
                return EmailVerificationCodeResponse(
                    email=email,
                    verified=False,
                    can_proceed=False,
                    message="인증 요청을 찾을 수 없습니다. 다시 인증 코드를 요청해주세요."
                )
            
            # Check if verification is expired
            if verification.is_expired():
                return EmailVerificationCodeResponse(
                    email=email,
                    verified=False,
                    can_proceed=False,
                    message="인증 코드가 만료되었습니다. 새로운 인증 코드를 요청해주세요."
                )
            
            # Check attempt limit
            if not verification.can_attempt():
                return EmailVerificationCodeResponse(
                    email=email,
                    verified=False,
                    can_proceed=False,
                    message="최대 시도 횟수를 초과했습니다. 새로운 인증 코드를 요청해주세요."
                )
            
            # Verify code
            if verification.code == code:
                # Success - mark as verified
                verification.mark_verified()
                await self.repository.update(verification)
                
                logger.info(f"Email verified successfully for {email}")
                return EmailVerificationCodeResponse(
                    email=email,
                    verified=True,
                    can_proceed=True,
                    message="이메일 인증이 완료되었습니다. 회원가입을 계속 진행해주세요."
                )
            else:
                # Wrong code - increment attempt
                verification.increment_attempt()
                await self.repository.update(verification)
                
                remaining_attempts = 5 - verification.attempt_count
                return EmailVerificationCodeResponse(
                    email=email,
                    verified=False,
                    can_proceed=False,
                    message=f"잘못된 인증 코드입니다. {remaining_attempts}번의 시도가 남았습니다."
                )
                
        except Exception as e:
            logger.error(f"Failed to verify email code for {request.email}: {str(e)}")
            return EmailVerificationCodeResponse(
                email=request.email,
                verified=False,
                can_proceed=False,
                message=f"인증 코드 확인 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def cleanup_expired_verifications(self) -> int:
        """Clean up expired verification codes."""
        return await self.repository.delete_expired()
    
    async def is_email_verified(self, email: str) -> bool:
        """Check if email has been verified and is ready for registration."""
        verification = await self.repository.get_by_email(email.lower())
        return verification is not None and verification.is_verified and not verification.is_expired()
    
    def _generate_verification_code(self) -> str:
        """Generate a random 6-digit verification code."""
        length = getattr(settings, 'email_verification_code_length', 6)
        characters = string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    def _create_email_content(self, code: str, email: str) -> Tuple[str, str]:
        """Create email content for verification."""
        subject = f"{settings.from_name} - 이메일 인증"
        
        expire_minutes = getattr(settings, 'email_verification_expire_minutes', 5)
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 40px;">
                <h1 style="color: #333; margin-bottom: 10px;">{settings.from_name}</h1>
                <p style="color: #666; margin: 0;">이메일 인증을 완료해주세요</p>
            </div>
            
            <div style="background-color: #f8f9fa; padding: 30px; border-radius: 10px; text-align: center;">
                <h2 style="color: #333; margin-bottom: 20px;">인증 코드</h2>
                <div style="background-color: white; padding: 20px; border-radius: 8px; display: inline-block; border: 2px solid #e9ecef;">
                    <span style="font-size: 32px; font-weight: bold; color: #007bff; letter-spacing: 5px;">{code}</span>
                </div>
                <p style="color: #666; margin-top: 20px; font-size: 14px;">
                    이 코드는 {expire_minutes}분 후에 만료됩니다.
                </p>
            </div>
            
            <div style="margin-top: 30px; padding: 20px; background-color: #fff3cd; border-radius: 8px;">
                <h3 style="color: #856404; margin-top: 0;">주의사항</h3>
                <ul style="color: #856404; margin: 0; padding-left: 20px;">
                    <li>이 이메일은 자동으로 발송된 메일입니다.</li>
                    <li>인증 코드를 다른 사람과 공유하지 마세요.</li>
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
    
    async def _send_email_smtp(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email using SMTP."""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{settings.from_name} <{settings.from_email}>"
            msg['To'] = to_email
            
            # Attach HTML content
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Connect to SMTP server and send
            with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
                if settings.smtp_use_tls:
                    server.starttls()
                
                if settings.smtp_username and settings.smtp_password:
                    server.login(settings.smtp_username, settings.smtp_password)
                
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"SMTP error when sending email to {to_email}: {str(e)}")
            return False