"""
File Upload API Module Unit Tests

Tests for file upload API endpoints including:
- Successful upload flow
- Request validation
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import UploadFile
from fastapi.testclient import TestClient
from src.routers.file_upload import router


@pytest.fixture
def client():
    """Create test client"""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router, prefix="/api/files")
    return TestClient(app)


class TestFileUploadAPI:
    """Test cases for file upload API"""

    @pytest.mark.asyncio
    async def test_successful_upload_flow(self):
        """Test successful file upload workflow"""
        # Mock file upload
        file_content = b"fake image data"
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.size = len(file_content)
        mock_file.read = AsyncMock(return_value=file_content)
        
        # Mock all dependencies
        with patch('src.routers.file_upload.validate_file_type', return_value=True), \
             patch('src.routers.file_upload.validate_file_size', return_value=True), \
             patch('src.routers.file_upload.validate_file_extension', return_value=True), \
             patch('src.routers.file_upload.generate_file_path', return_value="uploads/2025/06/test.jpg"), \
             patch('src.routers.file_upload.save_file_to_disk', return_value=True), \
             patch('src.routers.file_upload.extract_file_metadata', return_value={
                 "original_filename": "test.jpg",
                 "content_type": "image/jpeg",
                 "file_size": len(file_content),
                 "file_path": "uploads/2025/06/test.jpg"
             }), \
             patch('src.routers.file_upload.create_file_document', return_value={
                 "file_id": "test-uuid-123",
                 "original_filename": "test.jpg",
                 "content_type": "image/jpeg",
                 "file_size": len(file_content),
                 "file_path": "uploads/2025/06/test.jpg",
                 "status": "active"
             }), \
             patch('src.routers.file_upload.save_file_record', return_value=True):
            
            from src.routers.file_upload import upload_file
            
            result = await upload_file(mock_file)
            
            assert result["success"] is True
            assert result["file_id"] == "test-uuid-123"
            assert result["filename"] == "test.jpg"
            assert result["file_path"] == "uploads/2025/06/test.jpg"

    def test_upload_request_contract(self):
        """Test upload request validation"""
        # This test validates the API contract
        # In a real scenario, this would test with actual HTTP requests
        
        # Test valid file types
        valid_content_types = [
            "image/jpeg",
            "image/jpg", 
            "image/png",
            "image/gif",
            "image/webp"
        ]
        
        for content_type in valid_content_types:
            # Mock request validation would happen here
            # For now, we'll test the validation functions directly
            from src.services.file_validator import validate_file_type
            
            mock_file = Mock()
            mock_file.content_type = content_type
            assert validate_file_type(mock_file) is True
        
        # Test invalid file types
        invalid_content_types = [
            "application/pdf",
            "text/plain",
            "video/mp4",
            "application/exe"
        ]
        
        for content_type in invalid_content_types:
            mock_file = Mock()
            mock_file.content_type = content_type
            assert validate_file_type(mock_file) is False