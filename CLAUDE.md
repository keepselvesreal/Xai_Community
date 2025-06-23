# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture

This is a FastAPI-based content management system with a clean layered architecture following Domain-Driven Design principles. The project uses MongoDB with Motor for async database operations and implements TDD practices.

### Core Architecture Layers

**API Layer** (`routers/`) → **Service Layer** (`services/`) → **Repository Layer** (`repositories/`) → **Model Layer** (`models/`) → **Database** (MongoDB)

- Dependencies flow downward only (no circular dependencies)
- Each layer has single responsibility
- Business logic is contained in the service layer
- Data access is abstracted through repositories

### Key Components

**Database Foundation** (`src/database.py`, `src/config.py`, `src/models.py`, `src/indexes.py`):
- Uses Motor (async MongoDB driver) with connection pooling
- Pydantic for type-safe configuration management
- Beanie ODM for document modeling
- Comprehensive indexing strategy for performance optimization

**Configuration Management** (`src/config.py`):
- Environment-based configuration with Pydantic Settings
- Configuration file location: `config/.env` (not root `.env`)
- Type validation and environment-specific overrides

**Data Models** (`src/models.py`):
- Document models: User, Post, Comment, Reaction, Stats
- Request/Response models for API contracts
- Enum definitions for controlled values
- Pydantic validation with custom validators

**Database Indexes** (`src/indexes.py`):
- Query-optimized compound indexes
- Text search indexes with weighted fields
- Unique constraints for data integrity

## Development Commands

### Essential Commands (from Makefile)

```bash
# Dependencies and setup
make install          # Install dependencies with uv

# Development server
make dev             # Start development server with hot reload
make start           # Start production server

# Testing
make test            # Run all tests
make test-unit       # Run unit tests only
make test-integration # Run integration tests only
make test-cov        # Run tests with coverage report

# Code quality
make lint            # Run flake8 linting
make format          # Format code with black
make format-check    # Check formatting without changes

# Cleanup
make clean           # Remove cache files and temporary data
```

### Testing Individual Components

```bash
# Test specific files
uv run pytest tests/unit/test_config_settings.py -v
uv run pytest tests/unit/test_database_connection.py -v
uv run pytest tests/unit/test_models_validation.py -v
uv run pytest tests/unit/test_indexes_creation.py -v

# Run tests from project root
cd src && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
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

### File Organization Patterns

```
src/
├── models.py          # All data models (Document and Pydantic)
├── database.py        # Database connection and utilities  
├── indexes.py         # Database index definitions
├── config.py          # Configuration management
├── main.py            # FastAPI application setup
├── routers/           # API endpoints grouped by domain
├── services/          # Business logic layer
├── repositories/      # Data access layer
├── dependencies/      # FastAPI dependency injection
├── utils/             # Utility functions
└── exceptions/        # Custom exception classes
```

### Import Conventions

- Use absolute imports from `src/` root
- Avoid relative imports (`from ..module import`)
- Follow import order: standard library → third-party → local modules

### Testing Strategy

The project implements comprehensive TDD:
- **Unit Tests**: Test individual components in isolation with mocks
- **Integration Tests**: Test API endpoints with actual database interactions
- **Test Files**: Located in `tests/unit/` and `tests/integration/`
- **Fixtures**: Defined in `tests/conftest.py`

### Database Operations

- **Connection**: Managed through `src/database.py` Database class
- **Models**: Use Beanie ODM with Pydantic validation
- **Indexes**: Automatically created on application startup
- **Environment**: MongoDB Atlas connection with optimized settings

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

1. **Model Definition**: Add/update models in `src/models.py`
2. **Repository Layer**: Implement data access in `repositories/`
3. **Service Layer**: Add business logic in `services/`
4. **API Layer**: Create endpoints in `routers/`
5. **Dependencies**: Wire up dependency injection
6. **Tests**: Write comprehensive tests for each layer

### Database Schema Changes

1. Update models in `src/models.py`
2. Add/modify indexes in `src/indexes.py`
3. Create migration scripts if needed
4. Update tests to reflect schema changes

### Environment-Specific Behavior

The application automatically adjusts behavior based on the `environment` setting:
- **Development**: API docs enabled, verbose logging
- **Production**: API docs disabled, optimized settings
- **Testing**: Uses test database and mock configurations