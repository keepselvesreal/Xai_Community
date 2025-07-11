"""Repository for email verification operations."""

from typing import Optional
from datetime import datetime, timedelta
import logging

from ..models.email_verification import EmailVerification
from ..config import settings

logger = logging.getLogger(__name__)


class EmailVerificationRepository:
    """Repository for managing email verification data."""
    
    async def get_by_email(self, email: str) -> Optional[EmailVerification]:
        """Get email verification by email address."""
        try:
            return await EmailVerification.find_one(
                EmailVerification.email == email.lower()
            )
        except Exception as e:
            logger.error(f"Error getting email verification for {email}: {str(e)}")
            return None
    
    async def create(self, verification: EmailVerification) -> EmailVerification:
        """Create a new email verification."""
        try:
            # Delete any existing verification for this email first
            await self.delete_by_email(verification.email)
            
            # Save the new verification
            await verification.save()
            return verification
        except Exception as e:
            logger.error(f"Error creating email verification for {verification.email}: {str(e)}")
            raise
    
    async def update(self, verification: EmailVerification) -> EmailVerification:
        """Update an existing email verification."""
        try:
            await verification.save()
            return verification
        except Exception as e:
            logger.error(f"Error updating email verification for {verification.email}: {str(e)}")
            raise
    
    async def delete_by_email(self, email: str) -> bool:
        """Delete email verification by email address."""
        try:
            result = await EmailVerification.find(
                EmailVerification.email == email.lower()
            ).delete()
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting email verification for {email}: {str(e)}")
            return False
    
    async def delete_expired(self) -> int:
        """Delete all expired email verifications."""
        try:
            current_time = datetime.utcnow()
            result = await EmailVerification.find(
                EmailVerification.expires_at < current_time
            ).delete()
            
            deleted_count = result.deleted_count
            if deleted_count > 0:
                logger.info(f"Deleted {deleted_count} expired email verifications")
            
            return deleted_count
        except Exception as e:
            logger.error(f"Error deleting expired email verifications: {str(e)}")
            return 0
    
    async def count_by_email_today(self, email: str) -> int:
        """Count how many verifications were sent to this email today."""
        try:
            # Calculate start of today
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            count = await EmailVerification.find(
                EmailVerification.email == email.lower(),
                EmailVerification.created_at >= today_start
            ).count()
            
            return count
        except Exception as e:
            logger.error(f"Error counting daily verifications for {email}: {str(e)}")
            return 0
    
    async def cleanup_old_verifications(self, days_old: int = 1) -> int:
        """Clean up old verification records (beyond expiry)."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days_old)
            result = await EmailVerification.find(
                EmailVerification.created_at < cutoff_time
            ).delete()
            
            deleted_count = result.deleted_count
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old email verifications")
            
            return deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up old email verifications: {str(e)}")
            return 0