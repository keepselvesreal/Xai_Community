# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture

This is a full-stack web application with FastAPI backend and HTML-based frontend. The backend follows Domain-Driven Design principles with MongoDB and Motor for async database operations. The project implements TDD practices and task-driven development.

### Overall Project Structure

```
v5/
├── backend/               # FastAPI backend application
├── frontend/              # Remix React app (main production UI)
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

- **Primary UI**: `@frontend/` (Remix React) - Main production UI application currently in development
- **API Development Tool**: `frontend-prototypes/UI.html` - HTML dashboard for API testing and development
- **Frontend Architecture**: Full-featured Remix React application with TypeScript, Tailwind CSS, and comprehensive testing
- **Development Status**: Active UI development for production service using @frontend/ workspace
- **API Integration**: Frontend integrates with FastAPI backend through comprehensive API layer

### Current Implementation Status

- ✅ **Infrastructure Layer**: Database connection, models, configuration, indexes
- ✅ **API Layer**: Complete REST API with 5 routers (auth, posts, comments, files, content)
- ✅ **Service Layer**: Full business logic implementation across all domains
- ✅ **Repository Layer**: Complete data access layer with CRUD operations
- ✅ **File Management**: Complete file upload/processing system with validation
- ✅ **Rich Text Editor**: TDD-based editor with content processing pipeline
- ✅ **HTML UI**: Complete dashboard interface with API testing capabilities
- ✅ **Remix Frontend**: Main production UI with comprehensive component library and routing system

## Custom rules
### Communication 
- 모든 답변은 한국어로 작성해야 한다.
- 사용자 이름은 "태수"이고, 친구처럼 대한다.
- 사용자 요청에서 확실히 이해하지 못한 부분이 있다면 마음대로 해석해 작업을 진행하면 안된다. 헷갈리는 부분에 대해 사용자에게 질문하여 수행할 작업을 확실히 이해해야 한다.

### Execution 
- docs 폴더 내 파일 수정 시 기존 파일을 수정하지 않고, 새로운 버전의 파일을 만들어 수정 사항을 반영한다.
- 서버 실행 전에 이미 동작 중인 서버가 있는지 확인한다.
- 사용자가 제공한 정보도 비판적으로 검토하며, 무조건 신뢰하지 않는다.
- 패키지 설치 시 가상환경 등이 있는지 반드시 확인한다. 

### Coding
- 폴더나 파일을 만들 때는 기존 프로젝트 구조의 체계를 반영한다.
- 타입 검사를 활용하여 런타임 이전에 감지 가능한 오류를 사전에 방지한다.
- 오류 발생 가능성이 있는 부분에는 디버깅을 위한 코드 또는 로깅을 적절히 삽입한다.

### Frontend Workspace
- 현재 작업하는 UI 프로젝트 폴더는 @frontend/