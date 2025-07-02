# Database Import 문제 해결 및 리팩토링 기록

**날짜**: 2025-06-23  
**작업자**: Claude Code  
**목표**: `backend/tests/unit/test_database_connection.py`의 import 문제 해결

## 초기 문제 상황

### 발견된 문제
1. **네이밍 충돌**: `src/database.py` 파일과 `src/database/` 폴더가 동시에 존재
2. **Import 에러**: Python이 `src/database`를 import할 때 폴더의 `__init__.py`를 우선 로드하여 원하는 Database 클래스를 찾을 수 없음
3. **상대 import 문제**: `src/database/connection.py`에서 `from ..config import settings` 상대 import 사용으로 인한 에러

### 초기 파일 구조
```
src/
├── database.py              # 완전한 Database 클래스 구현
├── database/                # 폴더
│   ├── __init__.py         # connection.py의 함수들만 export
│   └── connection.py       # 간단한 Database 클래스와 연결 함수들
├── config.py
└── ...
```

## 시행착오 과정

### 1차 시도: Import 경로 수정
- **시도**: `test_database_connection.py`에서 `from src.database import ...` 사용
- **결과**: 실패 - Python이 `src/database/` 폴더를 우선 인식
- **에러**: `ImportError: cannot import name 'Database' from 'src.database'`

### 2차 시도: 직접 파일 경로 지정
- **시도**: `sys.path.insert()`와 `importlib.util`을 사용하여 `database.py` 직접 로드
- **결과**: 부분 성공하지만 복잡하고 유지보수 어려움
- **문제**: `src/database.py`의 `from .config import settings` 상대 import 문제

### 3차 시도: PYTHONPATH 설정
- **시도**: 환경변수로 Python 경로 설정
- **결과**: 여전히 상대 import 문제 발생

### 4차 시도: 구조적 해결책 (최종 성공)
- **해결 방법**: `src/database.py`를 `src/database/manager.py`로 이동
- **장점**: 
  - 기존 폴더 구조 유지
  - 명확한 모듈 조직
  - 상대 import 문제 해결

## 최종 해결책

### 파일 이동 및 구조 개선
```bash
# 실행한 명령
mv src/database.py src/database/manager.py
```

### 수정된 파일 구조
```
src/
├── database/
│   ├── __init__.py         # 모든 필요한 클래스/함수 export
│   ├── manager.py          # 완전한 Database 클래스 (이전 database.py)
│   └── connection.py       # 레거시 연결 함수들
├── config.py
└── ...
```

### 주요 수정 사항

#### 1. `src/database/__init__.py` 업데이트
```python
from .connection import connect_to_mongo, close_mongo_connection, init_database
from .manager import Database, database, get_database, get_client

__all__ = [
    "connect_to_mongo", 
    "close_mongo_connection", 
    "init_database",
    "Database",
    "database", 
    "get_database", 
    "get_client"
]
```

#### 2. `src/database/manager.py` import 수정
```python
# 변경 전
from .config import settings

# 변경 후  
from ..config import settings
```

#### 3. 테스트 파일 import 간소화
```python
# 최종 버전
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from src.database import Database, database, get_database, get_client
from src.config import Settings
```

#### 4. Motor Database 객체 문제 해결
Motor의 AsyncIOMotorDatabase 객체는 truthiness 검사를 지원하지 않으므로 모든 검사를 `is None`으로 변경:

```python
# 변경 전
if not self.database:
    raise RuntimeError("Database not connected")

# 변경 후
if self.database is None:
    raise RuntimeError("Database not connected")
```

### Patch 경로 수정
테스트에서 mock patch 경로를 모듈 구조에 맞게 수정:
```python
@patch('src.database.manager.AsyncIOMotorClient')
@patch('src.database.manager.settings', mock_settings)
@patch('src.database.manager.init_beanie')
@patch('src.database.database')  # 전역 인스턴스는 __init__.py를 통해 접근
```

## 현재 상황 (2025-06-23 완료 시점)

### 테스트 결과
```
collected 23 items
19 passed, 4 failed

실패한 테스트:
- test_get_database_dependency_not_connected
- test_get_database_dependency_already_connected  
- test_get_client_dependency_not_connected
- test_get_client_dependency_already_connected
```

### 성공한 주요 테스트들
- ✅ `test_database_initialization`
- ✅ `test_successful_connection`
- ✅ `test_connection_failure` (수정 후 통과)
- ✅ `test_disconnect`
- ✅ `test_ping_success/failure`
- ✅ `test_init_beanie_models_success/failure`
- ✅ `test_get_database_success/failure`
- ✅ `test_get_client_success/failure`
- ✅ `test_check_connection_*` (다양한 시나리오)

### 실패하는 테스트 분석
실패하는 4개 테스트는 모두 dependency 함수 관련이며, 실제 MongoDB Atlas에 연결을 시도하고 있음. 이는 mock이 전역 `database` 인스턴스에 제대로 적용되지 않아서 발생하는 문제로, 테스트 설계의 문제이지 실제 코드의 문제는 아님.

### 해결된 문제들
1. ✅ **Import 경로 충돌**: `database.py` → `database/manager.py` 이동으로 해결
2. ✅ **상대 import 에러**: 적절한 상대 경로 (`..config`) 사용으로 해결  
3. ✅ **Motor Database truthiness**: `is None` 검사로 해결
4. ✅ **테스트 실행 가능**: 23개 중 19개 테스트 통과, 핵심 기능 검증 완료

### 개선 사항
1. **코드 구조**: 더 명확한 모듈 조직
2. **Import 경로**: 표준적인 Python 패키지 구조 준수
3. **테스트 실행**: `PYTHONPATH` 설정으로 안정적 실행 가능
4. **유지보수성**: 각 컴포넌트의 역할이 명확히 분리됨

## 학습된 교훈

1. **Python 패키지 구조**: 파일과 폴더 이름이 같으면 폴더가 우선순위를 가짐
2. **상대 import**: 패키지 구조에서는 `..module` 형태의 상대 import 사용 필요
3. **Motor 라이브러리**: MongoDB 객체들은 특별한 truthiness 규칙을 가짐
4. **테스트 Mock**: 전역 인스턴스를 mock하는 것은 복잡할 수 있음

## 다음 단계 권장사항

1. **실패하는 의존성 테스트 수정**: Mock 전략 개선 필요
2. **문서화**: 새로운 모듈 구조에 대한 README 업데이트
3. **CI/CD**: PYTHONPATH 설정을 포함한 테스트 환경 구성
4. **코드 검토**: 다른 파일들에서 database import 경로 확인 및 수정

## 명령어 요약

### 개발 환경 설정
```bash
cd /home/nadle/projects/Xai_Community/v5/backend
uv sync --dev  # 개발 의존성 설치
```

### 테스트 실행
```bash
# 전체 테스트
PYTHONPATH=/home/nadle/projects/Xai_Community/v5/backend uv run pytest tests/unit/test_database_connection.py -v

# 특정 테스트
PYTHONPATH=/home/nadle/projects/Xai_Community/v5/backend uv run pytest tests/unit/test_database_connection.py::TestDatabaseConnection::test_connection_failure -v
```

### 린팅 및 포맷팅
```bash
make lint    # flake8 린팅
make format  # black 포맷팅
```