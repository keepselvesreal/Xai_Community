import smtplib
import secrets
import string
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

from ..config import settings
from ..models.core import User
from ..repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending verification emails and managing email verification."""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    def generate_verification_code(self) -> str:
        """Generate a random verification code."""
        length = settings.email_verification_code_length
        characters = string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    def create_verification_email_content(self, verification_code: str, email: str) -> tuple[str, str]:
        """Create email content for verification."""
        subject = f"{settings.from_name} - 이메일 인증"
        
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
                    <span style="font-size: 32px; font-weight: bold; color: #007bff; letter-spacing: 5px;">{verification_code}</span>
                </div>
                <p style="color: #666; margin-top: 20px; font-size: 14px;">
                    이 코드는 {settings.email_verification_expire_hours}시간 후에 만료됩니다.
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
    
    async def send_verification_email(self, email: str) -> tuple[bool, str]:
        """Send verification email to user."""
        try:
            # Generate verification code
            verification_code = self.generate_verification_code()
            
            # Calculate expiration time
            expires_at = datetime.utcnow() + timedelta(hours=settings.email_verification_expire_hours)
            
            # Update user with verification code
            user = await self.user_repository.get_user_by_email(email)
            if not user:
                return False, "사용자를 찾을 수 없습니다."
            
            await self.user_repository.set_email_verification_token(
                user.id, verification_code, expires_at
            )
            
            # Create email content
            subject, html_content = self.create_verification_email_content(verification_code, email)
            
            # Send email
            success = await self._send_email(email, subject, html_content)
            
            if success:
                logger.info(f"Verification email sent successfully to {email}")
                return True, "인증 코드가 이메일로 전송되었습니다."
            else:
                return False, "이메일 전송에 실패했습니다."
                
        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {str(e)}")
            return False, f"이메일 전송 중 오류가 발생했습니다: {str(e)}"
    
    async def verify_email_code(self, email: str, code: str) -> tuple[bool, str]:
        """Verify email verification code."""
        try:
            user = await self.user_repository.get_user_by_email(email)
            if not user:
                return False, "사용자를 찾을 수 없습니다."
            
            # Check if code exists and not expired
            if not user.email_verification_token:
                return False, "인증 코드가 설정되지 않았습니다."
            
            if user.email_verification_expires and user.email_verification_expires < datetime.utcnow():
                return False, "인증 코드가 만료되었습니다."
            
            # Verify code
            if user.email_verification_token != code:
                return False, "잘못된 인증 코드입니다."
            
            # Mark email as verified
            await self.user_repository.mark_email_verified(user.id)
            
            logger.info(f"Email verified successfully for {email}")
            return True, "이메일 인증이 완료되었습니다."
            
        except Exception as e:
            logger.error(f"Failed to verify email code for {email}: {str(e)}")
            return False, f"인증 코드 확인 중 오류가 발생했습니다: {str(e)}"
    
    async def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
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
    
    async def is_email_verified(self, email: str) -> bool:
        """Check if email is verified."""
        user = await self.user_repository.get_user_by_email(email)
        return user.email_verified if user else False
    
    async def resend_verification_email(self, email: str) -> tuple[bool, str]:
        """Resend verification email."""
        user = await self.user_repository.get_user_by_email(email)
        if not user:
            return False, "사용자를 찾을 수 없습니다."
        
        if user.email_verified:
            return False, "이미 인증된 이메일입니다."
        
        return await self.send_verification_email(email)