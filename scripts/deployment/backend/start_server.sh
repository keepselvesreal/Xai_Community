#!/bin/bash
# FastAPI 서버 안전 구동 스크립트

cd "$(dirname "$0")"
export PYTHONPATH="$(pwd)"

echo "FastAPI 서버를 시작합니다..."
echo "PYTHONPATH: $PYTHONPATH"

# 기존 서버 프로세스 확인
if lsof -i :8000 > /dev/null 2>&1; then
    echo "포트 8000이 이미 사용 중입니다."
    echo "기존 프로세스:"
    lsof -i :8000
    read -p "기존 프로세스를 종료하고 새로 시작하시겠습니까? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "기존 프로세스를 종료합니다..."
        pkill -f "uvicorn.*main:app" || true
        sleep 2
    else
        echo "서버 시작을 취소합니다."
        exit 0
    fi
fi

# 의존성 동기화
echo "의존성을 확인합니다..."
uv sync

# 서버 시작
echo "서버를 시작합니다..."
uv run python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000