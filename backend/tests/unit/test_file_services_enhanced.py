"""Enhanced unit tests for file services functionality."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from io import BytesIO
from nadle_backend.services.file_validator import FileValidator
from nadle_backend.services.file_storage import FileStorage
from nadle_backend.services.file_metadata import FileMetadataExtractor


class TestFileValidator:
    """Test file validation functionality."""
    
    @pytest.fixture
    def file_validator(self):
        """Create file validator instance."""
        return FileValidator()
    
    def test_validate_file_type_success(self, file_validator):
        """Test successful file type validation."""
        # Arrange
        allowed_types = ["image/jpeg", "image/png", "application/pdf"]
        
        # Act & Assert
        assert file_validator.validate_file_type("image/jpeg", allowed_types) is True
        assert file_validator.validate_file_type("image/png", allowed_types) is True
        assert file_validator.validate_file_type("application/pdf", allowed_types) is True
    
    def test_validate_file_type_failure(self, file_validator):
        """Test file type validation failure."""
        # Arrange
        allowed_types = ["image/jpeg", "image/png"]
        
        # Act & Assert
        assert file_validator.validate_file_type("application/pdf", allowed_types) is False
        assert file_validator.validate_file_type("text/plain", allowed_types) is False
        assert file_validator.validate_file_type("", allowed_types) is False
    
    def test_validate_file_size_success(self, file_validator):
        """Test successful file size validation."""
        # Arrange
        max_size = 5 * 1024 * 1024  # 5MB
        
        # Act & Assert
        assert file_validator.validate_file_size(1024, max_size) is True
        assert file_validator.validate_file_size(max_size, max_size) is True
        assert file_validator.validate_file_size(max_size - 1, max_size) is True
    
    def test_validate_file_size_failure(self, file_validator):
        """Test file size validation failure."""
        # Arrange
        max_size = 5 * 1024 * 1024  # 5MB
        
        # Act & Assert
        assert file_validator.validate_file_size(max_size + 1, max_size) is False
        assert file_validator.validate_file_size(10 * 1024 * 1024, max_size) is False
    
    def test_validate_filename_success(self, file_validator):
        """Test successful filename validation."""
        # Act & Assert
        assert file_validator.validate_filename("test.jpg") is True
        assert file_validator.validate_filename("document.pdf") is True
        assert file_validator.validate_filename("image_123.png") is True
        assert file_validator.validate_filename("file-name.txt") is True
    
    def test_validate_filename_failure(self, file_validator):
        """Test filename validation failure."""
        # Act & Assert
        assert file_validator.validate_filename("") is False
        assert file_validator.validate_filename(".hidden") is False
        assert file_validator.validate_filename("file<>name.txt") is False
        assert file_validator.validate_filename("file|name.txt") is False
        assert file_validator.validate_filename("file:name.txt") is False
    
    def test_sanitize_filename(self, file_validator):
        """Test filename sanitization."""
        # Act & Assert
        assert file_validator.sanitize_filename("test file.jpg") == "test_file.jpg"
        assert file_validator.sanitize_filename("file<>name.txt") == "filename.txt"
        assert file_validator.sanitize_filename("file|name.txt") == "filename.txt"
        assert file_validator.sanitize_filename("UPPERCASE.JPG") == "uppercase.jpg"
    
    def test_check_file_content_success(self, file_validator):
        """Test successful file content validation."""
        # Arrange
        # Mock JPEG file header
        jpeg_content = b'\xff\xd8\xff\xe0' + b'\x00' * 100
        file_obj = BytesIO(jpeg_content)
        
        # Act
        result = file_validator.check_file_content(file_obj, "image/jpeg")
        
        # Assert
        assert result is True
    
    def test_check_file_content_mismatch(self, file_validator):
        """Test file content validation with content/type mismatch."""
        # Arrange
        # Text content but claiming to be JPEG
        text_content = b'This is plain text content'
        file_obj = BytesIO(text_content)
        
        # Act
        result = file_validator.check_file_content(file_obj, "image/jpeg")
        
        # Assert
        assert result is False
    
    def test_validate_image_dimensions(self, file_validator):
        """Test image dimensions validation."""
        # Arrange
        with patch('PIL.Image.open') as mock_image_open:
            mock_image = MagicMock()
            mock_image.size = (800, 600)
            mock_image_open.return_value = mock_image
            
            file_obj = BytesIO(b'fake_image_data')
            max_width, max_height = 1920, 1080
            
            # Act
            result = file_validator.validate_image_dimensions(
                file_obj, max_width, max_height
            )
            
            # Assert
            assert result is True
    
    def test_validate_image_dimensions_too_large(self, file_validator):
        """Test image dimensions validation for oversized image."""
        # Arrange
        with patch('PIL.Image.open') as mock_image_open:
            mock_image = MagicMock()
            mock_image.size = (3840, 2160)  # 4K resolution
            mock_image_open.return_value = mock_image
            
            file_obj = BytesIO(b'fake_image_data')
            max_width, max_height = 1920, 1080  # Full HD limit
            
            # Act
            result = file_validator.validate_image_dimensions(
                file_obj, max_width, max_height
            )
            
            # Assert
            assert result is False


class TestFileStorage:
    """Test file storage functionality."""
    
    @pytest.fixture
    def file_storage(self):
        """Create file storage instance."""
        return FileStorage()
    
    @pytest.mark.asyncio
    async def test_save_file_success(self, file_storage):
        """Test successful file saving."""
        # Arrange
        file_content = b"test file content"
        filename = "test.txt"
        
        with patch('builtins.open', mock_open()) as mock_file, \
             patch('os.makedirs') as mock_makedirs, \
             patch('os.path.exists', return_value=False):
            
            # Act
            result = await file_storage.save_file(file_content, filename)
            
            # Assert
            assert result is not None
            assert "file_path" in result
            assert "file_id" in result
            mock_makedirs.assert_called()
            mock_file.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_file_directory_exists(self, file_storage):
        """Test file saving when directory already exists."""
        # Arrange
        file_content = b"test file content"
        filename = "test.txt"
        
        with patch('builtins.open', mock_open()) as mock_file, \
             patch('os.makedirs') as mock_makedirs, \
             patch('os.path.exists', return_value=True):
            
            # Act
            result = await file_storage.save_file(file_content, filename)
            
            # Assert
            assert result is not None
            mock_makedirs.assert_not_called()  # Directory already exists
            mock_file.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_file_success(self, file_storage):
        """Test successful file deletion."""
        # Arrange
        file_path = "/uploads/2024/01/test.txt"
        
        with patch('os.path.exists', return_value=True), \
             patch('os.remove') as mock_remove:
            
            # Act
            result = await file_storage.delete_file(file_path)
            
            # Assert
            assert result is True
            mock_remove.assert_called_once_with(file_path)
    
    @pytest.mark.asyncio
    async def test_delete_file_not_exists(self, file_storage):
        """Test file deletion when file doesn't exist."""
        # Arrange
        file_path = "/uploads/2024/01/nonexistent.txt"
        
        with patch('os.path.exists', return_value=False):
            
            # Act
            result = await file_storage.delete_file(file_path)
            
            # Assert
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_file_success(self, file_storage):
        """Test successful file retrieval."""
        # Arrange
        file_path = "/uploads/2024/01/test.txt"
        file_content = b"test file content"
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=file_content)) as mock_file:
            
            # Act
            result = await file_storage.get_file(file_path)
            
            # Assert
            assert result == file_content
            mock_file.assert_called_once_with(file_path, 'rb')
    
    @pytest.mark.asyncio
    async def test_get_file_not_exists(self, file_storage):
        """Test file retrieval when file doesn't exist."""
        # Arrange
        file_path = "/uploads/2024/01/nonexistent.txt"
        
        with patch('os.path.exists', return_value=False):
            
            # Act
            result = await file_storage.get_file(file_path)
            
            # Assert
            assert result is None
    
    @pytest.mark.asyncio
    async def test_list_files_success(self, file_storage):
        """Test successful file listing."""
        # Arrange
        directory = "/uploads/2024/01"
        files = ["file1.txt", "file2.jpg", "file3.pdf"]
        
        with patch('os.path.exists', return_value=True), \
             patch('os.listdir', return_value=files), \
             patch('os.path.isfile', return_value=True):
            
            # Act
            result = await file_storage.list_files(directory)
            
            # Assert
            assert len(result) == 3
            assert all(f in [r["filename"] for r in result] for f in files)
    
    @pytest.mark.asyncio
    async def test_get_file_info_success(self, file_storage):
        """Test successful file info retrieval."""
        # Arrange
        file_path = "/uploads/2024/01/test.txt"
        
        with patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=1024), \
             patch('os.path.getmtime', return_value=1640995200.0):  # 2022-01-01
            
            # Act
            result = await file_storage.get_file_info(file_path)
            
            # Assert
            assert result["size"] == 1024
            assert "created_at" in result
            assert "filename" in result
    
    def test_generate_file_path(self, file_storage):
        """Test file path generation."""
        # Arrange
        filename = "test.txt"
        
        # Act
        result = file_storage.generate_file_path(filename)
        
        # Assert
        assert filename in result
        assert "/uploads/" in result
        # Should include year and month in path
        current_year = str(datetime.now().year)
        current_month = f"{datetime.now().month:02d}"
        assert current_year in result
        assert current_month in result
    
    def test_generate_unique_filename(self, file_storage):
        """Test unique filename generation."""
        # Arrange
        original_filename = "test.txt"
        
        # Act
        result = file_storage.generate_unique_filename(original_filename)
        
        # Assert
        assert result != original_filename
        assert result.endswith(".txt")
        assert len(result) > len(original_filename)


class TestFileMetadataExtractor:
    """Test file metadata extraction functionality."""
    
    @pytest.fixture
    def metadata_extractor(self):
        """Create metadata extractor instance."""
        return FileMetadataExtractor()
    
    @pytest.mark.asyncio
    async def test_extract_image_metadata_success(self, metadata_extractor):
        """Test successful image metadata extraction."""
        # Arrange
        file_obj = BytesIO(b'fake_image_data')
        
        with patch('PIL.Image.open') as mock_image_open:
            mock_image = MagicMock()
            mock_image.size = (800, 600)
            mock_image.format = "JPEG"
            mock_image.mode = "RGB"
            mock_image_open.return_value = mock_image
            
            # Act
            result = await metadata_extractor.extract_image_metadata(file_obj)
            
            # Assert
            assert result["width"] == 800
            assert result["height"] == 600
            assert result["format"] == "JPEG"
            assert result["mode"] == "RGB"
    
    @pytest.mark.asyncio
    async def test_extract_image_metadata_failure(self, metadata_extractor):
        """Test image metadata extraction failure."""
        # Arrange
        file_obj = BytesIO(b'not_an_image')
        
        with patch('PIL.Image.open', side_effect=Exception("Cannot identify image")):
            
            # Act
            result = await metadata_extractor.extract_image_metadata(file_obj)
            
            # Assert
            assert result == {}
    
    @pytest.mark.asyncio
    async def test_extract_document_metadata_success(self, metadata_extractor):
        """Test successful document metadata extraction."""
        # Arrange
        file_path = "/uploads/test.pdf"
        file_content = b"fake pdf content"
        
        with patch('builtins.open', mock_open(read_data=file_content)), \
             patch('os.path.getsize', return_value=1024):
            
            # Act
            result = await metadata_extractor.extract_document_metadata(file_path)
            
            # Assert
            assert "file_size" in result
            assert result["file_size"] == 1024
            assert "file_type" in result
    
    @pytest.mark.asyncio
    async def test_extract_general_metadata_success(self, metadata_extractor):
        """Test successful general metadata extraction."""
        # Arrange
        file_path = "/uploads/test.txt"
        filename = "test.txt"
        content_type = "text/plain"
        
        with patch('os.path.getsize', return_value=512), \
             patch('os.path.getmtime', return_value=1640995200.0):
            
            # Act
            result = await metadata_extractor.extract_general_metadata(
                file_path, filename, content_type
            )
            
            # Assert
            assert result["filename"] == filename
            assert result["content_type"] == content_type
            assert result["file_size"] == 512
            assert "created_at" in result
            assert "file_extension" in result
    
    @pytest.mark.asyncio
    async def test_extract_all_metadata_image(self, metadata_extractor):
        """Test extracting all metadata for an image file."""
        # Arrange
        file_obj = BytesIO(b'fake_image_data')
        file_path = "/uploads/test.jpg"
        filename = "test.jpg"
        content_type = "image/jpeg"
        
        with patch.object(metadata_extractor, 'extract_general_metadata', 
                         new_callable=AsyncMock) as mock_general, \
             patch.object(metadata_extractor, 'extract_image_metadata', 
                         new_callable=AsyncMock) as mock_image:
            
            mock_general.return_value = {
                "filename": filename,
                "content_type": content_type,
                "file_size": 1024
            }
            mock_image.return_value = {
                "width": 800,
                "height": 600,
                "format": "JPEG"
            }
            
            # Act
            result = await metadata_extractor.extract_all_metadata(
                file_obj, file_path, filename, content_type
            )
            
            # Assert
            assert "general" in result
            assert "image" in result
            assert result["general"]["filename"] == filename
            assert result["image"]["width"] == 800
    
    @pytest.mark.asyncio
    async def test_extract_all_metadata_document(self, metadata_extractor):
        """Test extracting all metadata for a document file."""
        # Arrange
        file_obj = BytesIO(b'fake_pdf_data')
        file_path = "/uploads/test.pdf"
        filename = "test.pdf"
        content_type = "application/pdf"
        
        with patch.object(metadata_extractor, 'extract_general_metadata', 
                         new_callable=AsyncMock) as mock_general, \
             patch.object(metadata_extractor, 'extract_document_metadata', 
                         new_callable=AsyncMock) as mock_document:
            
            mock_general.return_value = {
                "filename": filename,
                "content_type": content_type,
                "file_size": 2048
            }
            mock_document.return_value = {
                "page_count": 5,
                "author": "Test Author"
            }
            
            # Act
            result = await metadata_extractor.extract_all_metadata(
                file_obj, file_path, filename, content_type
            )
            
            # Assert
            assert "general" in result
            assert "document" in result
            assert result["general"]["filename"] == filename
            assert result["document"]["page_count"] == 5