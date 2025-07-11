#!/bin/bash

# 시크릿 설정 스크립트
# 사용법: ./scripts/setup-secrets.sh

echo "🔐 XAI Community 시크릿 설정"

# .secrets 폴더 생성
mkdir -p .secrets

echo "📁 환경변수 파일 설정"

# Backend 환경변수 파일 확인
if [ ! -f backend/.env ]; then
    echo "📝 backend/.env 파일이 없습니다. .env.example을 복사하여 생성합니다."
    cp backend/.env.example backend/.env
    echo "⚠️  backend/.env 파일을 수정하여 실제 값을 설정하세요."
else
    echo "✅ backend/.env 파일이 이미 존재합니다."
fi

# Frontend 환경변수 파일 확인
if [ ! -f frontend/.env ]; then
    echo "📝 frontend/.env 파일이 없습니다. .env.example을 복사하여 생성합니다."
    cp frontend/.env.example frontend/.env
    echo "⚠️  frontend/.env 파일을 수정하여 실제 값을 설정하세요."
else
    echo "✅ frontend/.env 파일이 이미 존재합니다."
fi

echo ""
echo "🔑 Google Cloud 서비스 계정 키 확인"

# Google Cloud 서비스 계정 키 확인
if [ ! -f .secrets/service-account-key.json ]; then
    echo "⚠️  Google Cloud 서비스 계정 키가 없습니다."
    echo "   1. Google Cloud Console에서 서비스 계정 키 생성"
    echo "   2. .secrets/service-account-key.json으로 저장"
    echo "   3. 또는 GOOGLE_APPLICATION_CREDENTIALS_JSON 환경변수 설정"
else
    echo "✅ Google Cloud 서비스 계정 키가 존재합니다."
fi

echo ""
echo "🔒 권한 설정"

# 권한 설정
chmod 600 .secrets/* 2>/dev/null || true
chmod +x scripts/*.sh
chmod 600 backend/.env 2>/dev/null || true
chmod 600 frontend/.env 2>/dev/null || true

echo ""
echo "✅ 시크릿 설정 완료"
echo ""
echo "📋 다음 단계:"
echo "   1. backend/.env 파일에 실제 환경변수 값 입력"
echo "   2. frontend/.env 파일에 실제 환경변수 값 입력"
echo "   3. .secrets/service-account-key.json에 Google Cloud 키 저장"
echo "   4. 보안을 위해 환경변수는 시스템 레벨에서 관리 권장"
echo ""
echo "📖 자세한 내용은 docs/deployment.md를 참고하세요."