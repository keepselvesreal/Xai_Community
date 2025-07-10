#!/bin/bash

# 테스트 환경 변수 설정 및 테스트 실행 스크립트
export $(cat .env.test | grep -v "^#" | xargs)

echo "=== 테스트 환경 설정 완료 ==="
echo "Database: $DATABASE_NAME"
echo "Environment: $ENVIRONMENT"
echo ""

# 스크립트 디렉토리에서 backend 디렉토리로 이동
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

# Python 경로 설정
export PYTHONPATH="$BACKEND_DIR:$PYTHONPATH"

# 백엔드 디렉토리에서 테스트 실행
echo "=== 테스트 실행 시작 ==="
cd "$BACKEND_DIR"
uv run pytest tests/ -v --tb=short

echo "=== 테스트 실행 완료 ==="