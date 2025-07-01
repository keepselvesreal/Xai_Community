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
- **Frontend Folder**: @frontend/ for project frontend files

### Current Implementation Status

- ✅ **Infrastructure Layer**: Database connection, models, configuration, indexes
- ✅ **API Layer**: Complete REST API with 5 routers (auth, posts, comments, files, content)
- ✅ **Service Layer**: Full business logic implementation across all domains
- ✅ **Repository Layer**: Complete data access layer with CRUD operations
- ✅ **File Management**: Complete file upload/processing system with validation
- ✅ **Rich Text Editor**: TDD-based editor with content processing pipeline
- ✅ **HTML UI**: Complete dashboard interface with API testing capabilities
- ✅ **Remix Frontend**: Available for API development support when needed

[Rest of the file remains unchanged]