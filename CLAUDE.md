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
- ⚠️ **API Layer**: Structure exists but endpoints not implemented  
- ⚠️ **Service Layer**: Structure exists but business logic not implemented
- ⚠️ **Repository Layer**: Structure exists but data access methods not implemented
- ✅ **HTML UI**: Complete dashboard interface with API testing capabilities
- ✅ **Remix Frontend**: Available for API development support when needed

### Key Components

**Database Foundation** (`backend/src/database/connection.py`, `backend/src/config.py`):
- Uses Motor (async MongoDB driver) with connection pooling
- Pydantic for type-safe configuration management
- Beanie ODM for document modeling
- Database health checks and connection management

**Configuration Management** (`backend/src/config.py`):
- Environment-based configuration with Pydantic Settings
- Configuration file location: `backend/config/.env` (not root `.env`)
- Type validation and environment-specific overrides
- MongoDB Atlas connection with security validation

**Data Models** (`backend/src/models/core.py`):
- Document models: User, Post, Comment, Reaction, Stats
- Request/Response models for API contracts
- Enum definitions for controlled values
- Pydantic validation with custom validators

**Database Indexes** (`backend/src/database/manager.py`):
- Query-optimized compound indexes
- Text search indexes with weighted fields
- Unique constraints for data integrity
- Index management and creation utilities

**HTML Dashboard** (`frontend-prototypes/UI.html`):
- Complete web dashboard interface
- Built-in API testing functionality
- Authentication, posts, comments management UI
- Responsive design with mobile support
- JavaScript-based dynamic interactions

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

# Development server (when FastAPI app is implemented)
cd backend && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

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

1. **Environment Variables**: Located in `config/.env` (not root level)
2. **Secret Key**: Must be 32+ characters for production
3. **MongoDB Connection**: Configured for MongoDB Atlas with connection pooling
4. **Development vs Production**: Settings automatically adjust based on environment

### Backend File Organization

```
backend/
├── src/
│   ├── config.py                # Configuration management
│   ├── database/
│   │   ├── connection.py        # Database connection and utilities
│   │   └── manager.py           # Index management
│   ├── models/
│   │   └── core.py              # All data models (Document and Pydantic)
│   ├── routers/                 # API endpoints grouped by domain (empty)
│   ├── services/                # Business logic layer (empty)
│   ├── repositories/            # Data access layer (empty)
│   ├── dependencies/            # FastAPI dependency injection (empty)
│   ├── utils/                   # Utility functions (empty)
│   └── exceptions/              # Custom exception classes (empty)
├── main.py                      # FastAPI application setup (placeholder)
├── tests/                       # Test files
│   ├── unit/                    # Unit tests (implemented)
│   ├── integration/             # Integration tests (empty)
│   └── conftest.py              # Test fixtures
├── pyproject.toml               # Project dependencies
├── Makefile                     # Development commands
└── config/
    ├── .env                     # Environment variables
    └── .env.example             # Environment template
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

- Use absolute imports from `src/` root
- Avoid relative imports (`from ..module import`)
- Follow import order: standard library → third-party → local modules

### Testing Strategy

The project implements comprehensive TDD:
- **Unit Tests**: Test individual components in isolation with mocks
  - ✅ Configuration validation (`test_config_settings.py`)
  - ✅ Database connection (`test_database_connection.py`)
  - ✅ Model validation (`test_models_validation.py`)
  - ✅ Index creation (`test_indexes_creation.py`)
- **Integration Tests**: Test API endpoints with actual database interactions (planned)
- **Test Files**: Located in `backend/tests/unit/` and `backend/tests/integration/`
- **Fixtures**: Defined in `backend/tests/conftest.py`
- **Frontend Testing**: Manual testing using HTML UI dashboard
- **API Testing**: Built-in API testing interface in `frontend-prototypes/UI.html`

### Database Operations

- **Connection**: Managed through `backend/src/database/connection.py` Database class
- **Models**: Use Beanie ODM with Pydantic validation in `backend/src/models/core.py`
- **Indexes**: Managed through `backend/src/database/manager.py`, created on startup
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

- Database queries use optimized indexes (see `src/indexes.py`)
- Async/await pattern throughout for non-blocking operations
- Connection pooling configured for MongoDB
- Pagination implemented for list endpoints

## Common Development Patterns

### Adding New Features

1. **Model Definition**: Add/update models in `backend/src/models/core.py`
2. **Repository Layer**: Implement data access in `backend/src/repositories/`
3. **Service Layer**: Add business logic in `backend/src/services/`
4. **API Layer**: Create endpoints in `backend/src/routers/`
5. **Dependencies**: Wire up dependency injection in `backend/src/dependencies/`
6. **Tests**: Write comprehensive tests for each layer
7. **Frontend Integration**: Update `frontend-prototypes/UI.html` to use new APIs
8. **API Testing**: Add endpoint testing to HTML dashboard interface

### Database Schema Changes

1. Update models in `backend/src/models/core.py`
2. Add/modify indexes in `backend/src/database/manager.py`
3. Create migration scripts if needed
4. Update tests to reflect schema changes
5. Update HTML UI forms to match new schema
6. Test API integration with updated models

### Environment-Specific Behavior

The application automatically adjusts behavior based on the `environment` setting:
- **Development**: API docs enabled, verbose logging
- **Production**: API docs disabled, optimized settings
- **Testing**: Uses test database and mock configurations

## Response Guide
### 수행 작업 요약 제시
- 응답 마지막에는 아래 내용을 간략히 정리하여 제시
    - 수행한 작업
    - 진행 과정: 성공과 실패 여부가 아니라 진행 과정 자체 기술에 초점 