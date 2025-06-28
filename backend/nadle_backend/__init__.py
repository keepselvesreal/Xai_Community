"""
nadle_backend - FastAPI backend for content management system.

A comprehensive backend API built with FastAPI, MongoDB, and Beanie ODM.
Provides authentication, post management, comments, file uploads, and rich text content processing.
"""

__version__ = "0.1.0"
__author__ = "nadle"
__email__ = ""
__license__ = "MIT"

# Core application components
from .config import settings, get_settings

# Database components
from .database.connection import database
from .database.manager import IndexManager

# Models
from .models.core import (
    User, Post, Comment, PostStats, UserReaction, Stats, FileRecord
)

# Note: Specific classes can be imported individually as needed
# Example: from nadle_backend.services.auth_service import AuthService

__all__ = [
    # Version and metadata
    "__version__", "__author__", "__license__",
    
    # Configuration
    "settings", "get_settings",
    
    # Database
    "database", "IndexManager",
    
    # Models
    "User", "Post", "Comment", "PostStats", "UserReaction", "Stats", "FileRecord",
    
    # Package info
    "get_package_info",
]

# Package information
def get_package_info():
    """Get package information."""
    return {
        "name": "nadle_backend",
        "version": __version__,
        "author": __author__,
        "license": __license__,
        "description": __doc__.strip(),
    }