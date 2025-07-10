"""
File API Contract Validation Tests

Tests for API response contracts and schemas including:
- Upload response schema validation
- Error response format validation
"""

import pytest
from typing import Dict, Any


class TestFileAPIContract:
    """Test cases for file API contracts"""

    def test_upload_response_contract(self):
        """Test upload success response schema"""
        # Expected response schema for successful upload
        expected_response_schema = {
            "success": bool,
            "message": str,
            "file_id": str,
            "filename": str,
            "file_path": str,
            "file_size": int,
            "content_type": str
        }
        
        # Mock successful response
        mock_response = {
            "success": True,
            "message": "File uploaded successfully",
            "file_id": "550e8400-e29b-41d4-a716-446655440000",
            "filename": "test.jpg",
            "file_path": "uploads/2025/06/test.jpg",
            "file_size": 1024,
            "content_type": "image/jpeg"
        }
        
        # Validate response schema
        result = validate_upload_response(mock_response)
        assert result is True
        
        # Test missing required fields
        incomplete_response = {
            "success": True,
            "message": "File uploaded successfully"
            # Missing other required fields
        }
        
        result = validate_upload_response(incomplete_response)
        assert result is False
        
        # Test wrong data types
        wrong_type_response = {
            "success": "true",  # Should be bool, not string
            "message": "File uploaded successfully",
            "file_id": "test-uuid-123",
            "filename": "test.jpg",
            "file_path": "uploads/2025/06/test.jpg",
            "file_size": "1024",  # Should be int, not string
            "content_type": "image/jpeg"
        }
        
        result = validate_upload_response(wrong_type_response)
        assert result is False

    def test_error_response_contract(self):
        """Test error response schema"""
        # Expected error response schema
        expected_error_schema = {
            "detail": str
        }
        
        # Test standard error responses
        error_responses = [
            {"detail": "Invalid file type. Only image files (jpg, jpeg, png, gif, webp) are allowed."},
            {"detail": "File size too large. Maximum size is 5MB."},
            {"detail": "File extension does not match the file type."},
            {"detail": "Failed to save file to disk."},
            {"detail": "Failed to save file record to database."},
            {"detail": "An unexpected error occurred during file upload."}
        ]
        
        for error_response in error_responses:
            result = validate_error_response(error_response)
            assert result is True
        
        # Test invalid error response
        invalid_error = {
            "error": "Some error"  # Should be "detail", not "error"
        }
        
        result = validate_error_response(invalid_error)
        assert result is False
        
        # Test missing detail
        empty_error = {}
        result = validate_error_response(empty_error)
        assert result is False


def validate_upload_response(response: Dict[str, Any]) -> bool:
    """
    Validate upload success response schema
    
    Args:
        response: Response dictionary to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    required_fields = {
        "success": bool,
        "message": str,
        "file_id": str,
        "filename": str,
        "file_path": str,
        "file_size": int,
        "content_type": str
    }
    
    try:
        # Check all required fields exist
        for field, expected_type in required_fields.items():
            if field not in response:
                return False
            if not isinstance(response[field], expected_type):
                return False
        
        # Validate specific field constraints
        if not response["success"]:  # Success response should have success=True
            return False
            
        if len(response["file_id"]) != 36:  # UUID length with hyphens
            return False
            
        if response["file_size"] <= 0:  # File size should be positive
            return False
            
        return True
        
    except Exception:
        return False


def validate_error_response(response: Dict[str, Any]) -> bool:
    """
    Validate error response schema
    
    Args:
        response: Error response dictionary to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Check required field exists
        if "detail" not in response:
            return False
            
        # Check detail is a non-empty string
        if not isinstance(response["detail"], str) or not response["detail"].strip():
            return False
            
        return True
        
    except Exception:
        return False