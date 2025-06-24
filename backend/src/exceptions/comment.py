"""Comment-related exception classes."""

from src.exceptions.base import BaseAppException


class CommentNotFoundError(BaseAppException):
    """Exception raised when a comment is not found."""
    
    def __init__(self, comment_id: str = None, **kwargs):
        self.comment_id = comment_id
        if comment_id:
            message = f"Comment with ID '{comment_id}' not found"
        else:
            message = "Comment not found"
        
        super().__init__(
            message=message,
            status_code=404,
            error_code="COMMENT_NOT_FOUND",
            details={"comment_id": comment_id, **kwargs}
        )


class CommentPermissionError(BaseAppException):
    """Exception raised when user lacks permission for comment operation."""
    
    def __init__(self, action: str = "access", comment_id: str = None, user_id: str = None):
        self.action = action
        self.comment_id = comment_id
        self.user_id = user_id
        
        message = f"Permission denied for comment {action}"
        if comment_id:
            message += f" on comment '{comment_id}'"
        
        super().__init__(
            message=message,
            status_code=403,
            error_code="COMMENT_PERMISSION_DENIED",
            details={
                "action": action,
                "comment_id": comment_id,
                "user_id": user_id
            }
        )


class CommentValidationError(BaseAppException):
    """Exception raised when comment validation fails."""
    
    def __init__(self, field: str, value: str = None, **kwargs):
        self.field = field
        self.value = value
        
        message = f"Invalid comment {field}"
        if value:
            message += f": '{value}'"
        
        super().__init__(
            message=message,
            status_code=400,
            error_code="COMMENT_VALIDATION_ERROR",
            details={"field": field, "value": value, **kwargs}
        )


class CommentDepthExceededError(BaseAppException):
    """Exception raised when comment reply depth exceeds limit."""
    
    def __init__(self, max_depth: int = 2, current_depth: int = None):
        self.max_depth = max_depth
        self.current_depth = current_depth
        
        message = f"Comment reply depth exceeds maximum allowed depth of {max_depth}"
        if current_depth is not None:
            message += f" (attempted depth: {current_depth})"
        
        super().__init__(
            message=message,
            status_code=400,
            error_code="COMMENT_DEPTH_EXCEEDED",
            details={
                "max_depth": max_depth,
                "current_depth": current_depth
            }
        )


class CommentStatusError(BaseAppException):
    """Exception raised when comment status is invalid for operation."""
    
    def __init__(self, status: str, operation: str, comment_id: str = None):
        self.status = status
        self.operation = operation
        self.comment_id = comment_id
        
        message = f"Cannot {operation} comment with status '{status}'"
        if comment_id:
            message += f" (comment ID: {comment_id})"
        
        super().__init__(
            message=message,
            status_code=400,
            error_code="COMMENT_STATUS_ERROR",
            details={
                "status": status,
                "operation": operation,
                "comment_id": comment_id
            }
        )