"""
작업 시간: 2025-07-25 09:20:00 KST
작업 버전: v1.0.0
주요 컴포넌트들: EmailVerificationTokenRepository
주요 함수들:
- create_token_verification: 토큰 기반 이메일 인증 생성 (L30-40)
- get_by_token: 토큰으로 인증 정보 조회 (L42-48) 
- get_by_email: 이메일로 인증 정보 조회 (L50-56)
- mark_as_verified: 이메일 인증 완료 처리 (L58-65)
- delete_expired: 만료된 토큰 정리 (L67-73)
- cleanup_old_tokens: 특정 이메일의 기존 토큰 정리 (L75-81)
관련 파일들:
- models/email_verification.py: EmailVerificationToken 모델
- services/email_verification_token_service.py: 비즈니스 로직
"""

from datetime import datetime
from typing import Optional
from ..models.email_verification import EmailVerificationToken


class EmailVerificationTokenRepository:
    """Repository for token-based email verification operations."""

    async def create_token_verification(
        self, email: str, expire_minutes: int = None, created_ip: str = None
    ) -> EmailVerificationToken:
        """Create a new token-based email verification."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"🗃️ Repository: Creating token verification for {email}")
            logger.info(f"🗃️ Repository: expire_minutes={expire_minutes}, created_ip={created_ip}")
            
            # Remove any existing tokens for this email
            logger.info(f"🗃️ Repository: Cleaning up old tokens...")
            deleted_count = await self.cleanup_old_tokens(email)
            logger.info(f"🗃️ Repository: Deleted {deleted_count} old tokens")
            
            # Create new token verification
            logger.info(f"🗃️ Repository: Creating EmailVerificationToken instance...")
            verification = EmailVerificationToken.create_token_verification(
                email=email, expire_minutes=expire_minutes, created_ip=created_ip
            )
            logger.info(f"🗃️ Repository: Token instance created: {verification.token[:10]}...")
            
            logger.info(f"🗃️ Repository: Saving to database...")
            await verification.save()
            logger.info(f"🗃️ Repository: Saved successfully with ID: {verification.id}")
            
            return verification
            
        except Exception as e:
            logger.error(f"❌ Repository error: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"📍 Repository traceback: {traceback.format_exc()}")
            raise e

    async def get_by_token(self, token: str) -> Optional[EmailVerificationToken]:
        """Get verification by token."""
        return await EmailVerificationToken.find_one(
            EmailVerificationToken.token == token
        )

    async def get_by_email(self, email: str) -> Optional[EmailVerificationToken]:
        """Get the latest verification by email."""
        return await EmailVerificationToken.find_one(
            EmailVerificationToken.email == email.lower(),
            sort=[("created_at", -1)]  # Get the latest one
        )

    async def mark_as_verified(self, token: str) -> bool:
        """Mark email verification as completed."""
        verification = await self.get_by_token(token)
        if verification and not verification.is_expired():
            verification.mark_verified()
            await verification.save()
            return True
        return False

    async def delete_expired(self) -> int:
        """Delete expired verification tokens."""
        result = await EmailVerificationToken.find(
            EmailVerificationToken.expires_at < datetime.utcnow()
        ).delete()
        return result.deleted_count

    async def cleanup_old_tokens(self, email: str) -> int:
        """Remove existing tokens for an email address."""
        result = await EmailVerificationToken.find(
            EmailVerificationToken.email == email.lower()
        ).delete()
        return result.deleted_count