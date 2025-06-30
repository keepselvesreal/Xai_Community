# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture

This is a full-stack web application with FastAPI backend and HTML-based frontend. The backend follows Domain-Driven Design principles with MongoDB and Motor for async database operations. The project implements TDD practices and task-driven development.

### Overall Project Structure

```
v5/
├── backend/               # FastAPI backend application
├── frontend/              # Remix React app (development/testing tool)
├── frontend-prototypes/   # HTML UI for API integration
│   └── UI.html           # Complete dashboard interface with API testing
├── docs/                  # Documentation files
├── tasks/                 # Task management system
├── records/               # Project records and logs
└── references/            # Reference materials
```

### Backend Architecture Layers

**API Layer** (`routers/`) → **Service Layer** (`services/`) → **Repository Layer** (`repositories/`) → **Model Layer** (`models/`) → **Database** (MongoDB)

- Dependencies flow downward only (no circular dependencies)
- Each layer has single responsibility
- Business logic is contained in the service layer
- Data access is abstracted through repositories

### Frontend Strategy

- **Primary UI**: `frontend-prototypes/UI.html` - Single-page dashboard application for production use
- **API Development Support**: `frontend/` (Remix React) - Available for API development assistance when needed
- **API Integration**: HTML UI will be integrated with FastAPI backend endpoints
- **Testing Interface**: Built-in API testing functionality in HTML dashboard

### Current Implementation Status

- ✅ **Infrastructure Layer**: Database connection, models, configuration, indexes
- ✅ **API Layer**: Complete REST API with 5 routers (auth, posts, comments, files, content)
- ✅ **Service Layer**: Full business logic implementation across all domains
- ✅ **Repository Layer**: Complete data access layer with CRUD operations
- ✅ **File Management**: Complete file upload/processing system with validation
- ✅ **Rich Text Editor**: TDD-based editor with content processing pipeline
- ✅ **HTML UI**: Complete dashboard interface with API testing capabilities
- ✅ **Remix Frontend**: Available for API development support when needed

### Key Components

**Database Foundation** (`backend/nadle_backend/database/connection.py`, `backend/nadle_backend/config.py`):
- Uses Motor (async MongoDB driver) with connection pooling
- Pydantic for type-safe configuration management
- Beanie ODM for document modeling
- Database health checks and connection management

**Configuration Management** (`backend/nadle_backend/config.py`):
- Environment-based configuration with Pydantic Settings
- Configuration file location: `backend/.env` (at backend root level)
- Type validation and environment-specific overrides
- MongoDB Atlas connection with security validation

**Data Models** (`backend/nadle_backend/models/core.py`, `backend/nadle_backend/models/content.py`):
- Document models: User, Post, Comment, PostStats, UserReaction, Stats, FileRecord
- Request/Response models for API contracts
- Rich text content processing models
- Enum definitions for controlled values
- Pydantic validation with custom validators

**Database Indexes** (`backend/nadle_backend/database/manager.py`):
- Query-optimized compound indexes
- Text search indexes with weighted fields
- Unique constraints for data integrity
- Index management and creation utilities

**HTML Dashboard** (`frontend-prototypes/UI.html`):
- Complete web dashboard interface (7,705+ lines)
- Built-in API testing functionality
- Authentication, posts, comments management UI
- File upload and rich text editor integration
- Responsive design with mobile support
- JavaScript-based dynamic interactions

**File Management System** (`backend/nadle_backend/services/file_*.py`, `backend/nadle_backend/routers/file_upload.py`):
- Complete file upload API with validation
- File storage and metadata management
- Image processing and optimization
- Secure file serving with access control

**Rich Text Editor System** (`backend/nadle_backend/services/content_service.py`, `backend/nadle_backend/routers/content.py`):
- TDD-based rich text editor implementation
- Content processing and sanitization pipeline
- HTML content validation and transformation
- Editor state management and persistence

## Development Commands

### Backend Commands (from Makefile)

```bash
# Navigate to backend directory first
cd backend

# Dependencies and setup
make install          # Install dependencies with uv

# Development server (when FastAPI app is ready)
make dev             # Start development server with hot reload
make start           # Start production server

# Testing
make test            # Run all tests
make test-unit       # Run unit tests only
make test-integration # Run integration tests only (empty)
make test-cov        # Run tests with coverage report

# Code quality
make lint            # Run flake8 linting
make format          # Format code with black
make format-check    # Check formatting without changes

# Cleanup
make clean           # Remove cache files and temporary data
```

### Frontend Commands

```bash
# Primary UI (HTML)
# Simply open frontend-prototypes/UI.html in browser
# No build step required for HTML/CSS/JavaScript UI

# API Development Support (Remix React) - use when needed
cd frontend
npm run dev          # Start Remix development server (if needed for API development)
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # ESLint checking
npm run typecheck    # TypeScript checking
```

### Testing Individual Components

```bash
# Test specific files
cd backend && uv run pytest tests/unit/test_config_settings.py -v
cd backend && uv run pytest tests/unit/test_database_connection.py -v
cd backend && uv run pytest tests/unit/test_models_validation.py -v
cd backend && uv run pytest tests/unit/test_indexes_creation.py -v

# Test feature-specific components
cd backend && uv run pytest tests/unit/test_auth_*.py -v
cd backend && uv run pytest tests/unit/test_posts_*.py -v
cd backend && uv run pytest tests/unit/test_comments_*.py -v
cd backend && uv run pytest tests/unit/test_file_*.py -v
cd backend && uv run pytest tests/unit/test_content_*.py -v

# Integration tests
cd backend && uv run pytest tests/integration/ -v

# Development server (when FastAPI app is implemented)
cd backend && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
# Alternative using CLI interface
cd backend && uv run python main.py
# Or using the package CLI
cd backend && uv run nadle-backend

# Frontend development server (development tool)
cd frontend && npm run dev

# HTML UI testing
# Open frontend-prototypes/UI.html in browser for UI testing
```

## Development Workflow

### Task-Driven Development

The project follows a structured task system located in `tasks/` directory:
- Tasks are organized by feature groups (core-infrastructure, content-management, system-integration)
- Each task includes TDD requirements with specific test functions
- Implementation order: Model → Repository → Service → Router → Tests

### Configuration Setup

1. **Environment Variables**: Located in `backend/.env` (at backend root level)
2. **Secret Key**: Must be 32+ characters for production
3. **MongoDB Connection**: Configured for MongoDB Atlas with connection pooling
4. **Development vs Production**: Settings automatically adjust based on environment

### Backend File Organization

```
backend/
├── nadle_backend/               # Main package directory
│   ├── config.py                # Configuration management
│   ├── cli.py                   # CLI interface
│   ├── database/
│   │   ├── connection.py        # Database connection and utilities
│   │   └── manager.py           # Index management
│   ├── models/
│   │   ├── core.py              # All data models (Document and Pydantic)
│   │   └── content.py           # Rich text content processing models
│   ├── routers/                 # API endpoints grouped by domain
│   │   ├── auth.py              # Authentication endpoints
│   │   ├── posts.py             # Post management API
│   │   ├── comments.py          # Comment operations API
│   │   ├── file_upload.py       # File management API
│   │   └── content.py           # Rich text editor API
│   ├── services/                # Business logic layer
│   │   ├── auth_service.py      # Authentication logic
│   │   ├── posts_service.py     # Post management logic
│   │   ├── comments_service.py  # Comment operations logic
│   │   ├── content_service.py   # Rich text processing
│   │   ├── email_service.py     # Email operations
│   │   ├── file_validator.py    # File validation logic
│   │   ├── file_storage.py      # File storage management
│   │   └── file_metadata.py     # File metadata extraction
│   ├── repositories/            # Data access layer
│   │   ├── user_repository.py   # User data operations
│   │   ├── post_repository.py   # Post data operations
│   │   ├── comment_repository.py # Comment data operations
│   │   └── file_repository.py   # File data operations
│   ├── dependencies/            # FastAPI dependency injection
│   │   └── auth.py             # Authentication dependencies
│   ├── utils/                  # Utility functions
│   │   ├── jwt.py              # JWT token management
│   │   ├── password.py         # Password hashing
│   │   └── permissions.py      # Permission checking
│   └── exceptions/             # Custom exception classes
│       ├── auth_exceptions.py  # Authentication errors
│       ├── user_exceptions.py  # User operation errors
│       ├── post_exceptions.py  # Post operation errors
│       └── comment_exceptions.py # Comment operation errors
├── main.py                      # FastAPI application setup (complete)
├── start_server.sh              # Server startup script
├── tests/                       # Test files
│   ├── unit/                    # Unit tests (40+ test files)
│   ├── integration/             # Integration tests (implemented)
│   └── conftest.py              # Test fixtures
├── pyproject.toml               # Project dependencies and package configuration
├── Makefile                     # Development commands
├── .env                         # Environment variables
└── .env.example                 # Environment template
```

### Frontend Organization

```
frontend-prototypes/
└── UI.html                      # Complete dashboard interface

frontend/                        # Development tool (Remix React)
├── app/                         # Remix application
├── package.json                 # Frontend dependencies
└── [standard Remix structure]   # Full React application
```

### Import Conventions

- Use absolute imports from `nadle_backend/` root
- Avoid relative imports (`from ..module import`)
- Follow import order: standard library → third-party → local modules
- Example: `from nadle_backend.models.core import User`

### Testing Strategy

The project implements comprehensive TDD:
- **Unit Tests**: Test individual components in isolation with mocks (40+ test files)
  - ✅ Configuration validation (`test_config_settings.py`)
  - ✅ Database connection (`test_database_connection.py`)
  - ✅ Model validation (`test_models_validation.py`)
  - ✅ Index creation (`test_indexes_creation.py`)
  - ✅ Authentication logic (27+ auth test functions)
  - ✅ Post operations (`test_posts_*.py`)
  - ✅ Comment operations (`test_comments_*.py`)
  - ✅ File management (`test_file_*.py`)
  - ✅ Content processing (`test_content_*.py`)
- **Integration Tests**: Test API endpoints with actual database interactions
  - ✅ API contract testing
  - ✅ End-to-end workflow testing
  - ✅ File upload integration testing
- **Test Files**: Located in `backend/tests/unit/` and `backend/tests/integration/`
- **Test Coverage**: 90%+ for core functionality
- **Fixtures**: Defined in `backend/tests/conftest.py`
- **Frontend Testing**: Manual testing using HTML UI dashboard
- **API Testing**: Built-in API testing interface in `frontend-prototypes/UI.html`

### Database Operations

- **Connection**: Managed through `backend/nadle_backend/database/connection.py` Database class
- **Models**: Use Beanie ODM with Pydantic validation in `backend/nadle_backend/models/core.py`
- **Indexes**: Managed through `backend/nadle_backend/database/manager.py`, created on startup
- **Environment**: MongoDB Atlas connection with optimized settings
- **Health Checks**: Built-in connection monitoring and validation

## Code Standards

### Naming Conventions

- **Files**: snake_case (e.g., `user_repository.py`)
- **Classes**: PascalCase (e.g., `UserRepository`)
- **Functions/Variables**: snake_case (e.g., `get_user_by_id`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_PAGE_SIZE`)

### Error Handling

- Use custom exceptions from `exceptions/` module
- Implement proper error responses in API routes
- Log errors with appropriate levels using Python logging

### Performance Considerations

- Database queries use optimized indexes (see `nadle_backend/database/manager.py`)
- Async/await pattern throughout for non-blocking operations
- Connection pooling configured for MongoDB
- Pagination implemented for list endpoints

## Common Development Patterns

### Adding New Features

1. **Model Definition**: Add/update models in `backend/nadle_backend/models/core.py` or create new model files
2. **Repository Layer**: Implement data access in `backend/nadle_backend/repositories/` (follow existing patterns)
3. **Service Layer**: Add business logic in `backend/nadle_backend/services/` (include validation and processing)
4. **API Layer**: Create endpoints in `backend/nadle_backend/routers/` (follow FastAPI conventions)
5. **Dependencies**: Wire up dependency injection in `backend/nadle_backend/dependencies/`
6. **Exception Handling**: Add custom exceptions in `backend/nadle_backend/exceptions/`
7. **Utils**: Add utility functions in `backend/nadle_backend/utils/` if needed
8. **Tests**: Write comprehensive tests for each layer (TDD approach)
9. **Frontend Integration**: Update `frontend-prototypes/UI.html` to use new APIs
10. **API Testing**: Add endpoint testing to HTML dashboard interface

### Database Schema Changes

1. Update models in `backend/nadle_backend/models/core.py`
2. Add/modify indexes in `backend/nadle_backend/database/manager.py`
3. Create migration scripts if needed
4. Update tests to reflect schema changes
5. Update HTML UI forms to match new schema
6. Test API integration with updated models

### Environment-Specific Behavior

The application automatically adjusts behavior based on the `environment` setting:
- **Development**: API docs enabled, verbose logging
- **Production**: API docs disabled, optimized settings
- **Testing**: Uses test database and mock configurations

## Language Preferences

### Multilingual Support
- 한국어로 답변 가능 (can respond in Korean)
- Will use Korean when specifically requested
- Default communication is in English
- Supports code and technical discussions in multiple languages