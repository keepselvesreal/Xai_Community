#!/bin/bash

# 테스트 환경 변수 설정 및 테스트 실행 스크립트
export $(cat .env.test | grep -v "^#" | xargs)

echo "=== 테스트 환경 설정 완료 ==="
echo "Database: $DATABASE_NAME"
echo "Environment: $ENVIRONMENT"
echo ""

# Python 경로 설정
export PYTHONPATH="/home/nadle/projects/Xai_Community/v5/backend:$PYTHONPATH"

# 테스트 실행
echo "=== 테스트 실행 시작 ==="
uv run pytest tests/ -v --tb=short

echo "=== 테스트 실행 완료 ==="