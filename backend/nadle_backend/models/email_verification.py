"""Email verification models for signup process."""

from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from beanie import Document, Indexed
from pymongo import ASCENDING

from ..config import settings


class EmailVerificationData(BaseModel):
    """Data model for email verification (used for validation and business logic)."""
    
    # Core fields
    email: str = Field(..., description="Email address being verified")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")
    
    # Timing fields
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When verification was created")
    expires_at: datetime = Field(..., description="When verification expires")
    
    # Rate limiting and security
    attempt_count: int = Field(default=0, description="Number of verification attempts")
    is_verified: bool = Field(default=False, description="Whether email has been verified")
    last_attempt_at: Optional[datetime] = Field(default=None, description="Last verification attempt time")
    
    # IP tracking for security (optional)
    created_ip: Optional[str] = Field(default=None, description="IP address that created verification")
    
    def is_expired(self) -> bool:
        """Check if verification code has expired."""
        return datetime.utcnow() > self.expires_at
    
    def can_attempt(self) -> bool:
        """Check if user can still attempt verification (rate limiting)."""
        max_attempts = getattr(settings, 'email_verification_max_attempts', 5)
        return self.attempt_count < max_attempts
    
    def increment_attempt(self) -> None:
        """Increment attempt count and update last attempt time."""
        self.attempt_count += 1
        self.last_attempt_at = datetime.utcnow()
    
    def mark_verified(self) -> None:
        """Mark email as verified."""
        self.is_verified = True
        self.last_attempt_at = datetime.utcnow()
    
    def time_until_expiry(self) -> int:
        """Get minutes until expiry."""
        if self.is_expired():
            return 0
        delta = self.expires_at - datetime.utcnow()
        return max(0, int(delta.total_seconds() / 60))
    
    @classmethod
    def create_verification(
        cls, 
        email: str, 
        code: str, 
        expire_minutes: int = None,
        created_ip: str = None
    ) -> "EmailVerificationData":
        """Create a new email verification instance."""
        if expire_minutes is None:
            expire_minutes = getattr(settings, 'email_verification_expire_minutes', 5)
            
        expires_at = datetime.utcnow() + timedelta(minutes=expire_minutes)
        
        return cls(
            email=email.lower(),
            code=code,
            expires_at=expires_at,
            created_ip=created_ip
        )


class EmailVerificationCreate(BaseModel):
    """Request model for creating email verification."""
    email: EmailStr = Field(..., description="Email address to verify")


class EmailVerificationResponse(BaseModel):
    """Response model for email verification operations."""
    success: bool = Field(..., description="Whether operation was successful")
    email: str = Field(..., description="Email address")
    code_sent: bool = Field(..., description="Whether verification code was sent")
    expires_in_minutes: int = Field(..., description="Minutes until code expires")
    can_resend: bool = Field(..., description="Whether user can resend code")
    message: str = Field(..., description="User-friendly message")


class EmailVerificationCodeRequest(BaseModel):
    """Request model for verifying email code."""
    email: EmailStr = Field(..., description="Email address")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")


class EmailVerificationCodeResponse(BaseModel):
    """Response model for email code verification."""
    email: str = Field(..., description="Email address")
    verified: bool = Field(..., description="Whether verification was successful")
    can_proceed: bool = Field(..., description="Whether user can proceed to registration")
    message: str = Field(..., description="User-friendly message")


class EmailVerification(Document, EmailVerificationData):
    """Email verification document for temporary storage during signup."""
    
    # Core fields (inheriting from EmailVerificationData but with Document-specific types)
    email: Indexed(str, unique=True) = Field(..., description="Email address being verified")
    
    class Settings:
        """Beanie document settings."""
        name = "email_verifications"
        indexes = [
            [("email", ASCENDING)],
            [("expires_at", ASCENDING)],  # For TTL index
            [("created_at", ASCENDING)],
        ]
    
    @classmethod
    def create_verification(
        cls, 
        email: str, 
        code: str, 
        expire_minutes: int = None,
        created_ip: str = None
    ) -> "EmailVerification":
        """Create a new email verification document instance."""
        if expire_minutes is None:
            expire_minutes = getattr(settings, 'email_verification_expire_minutes', 5)
            
        expires_at = datetime.utcnow() + timedelta(minutes=expire_minutes)
        
        return cls(
            email=email.lower(),
            code=code,
            expires_at=expires_at,
            created_ip=created_ip
        )