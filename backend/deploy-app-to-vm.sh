#!/bin/bash
# VM에 애플리케이션 배포하는 스크립트

set -e

# 환경변수 설정
export MONGODB_URL=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/mongodb-url" -H "Metadata-Flavor: Google")
export SECRET_KEY=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/secret-key" -H "Metadata-Flavor: Google")
export DATABASE_NAME=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/database-name" -H "Metadata-Flavor: Google")

# 애플리케이션 디렉토리로 이동
cd /app

# 기존 컨테이너 정리
docker stop xai-backend || true
docker rm xai-backend || true

# 새 컨테이너 실행
docker run -d \
    --name xai-backend \
    --restart unless-stopped \
    -p 8080:8080 \
    -e MONGODB_URL="$MONGODB_URL" \
    -e SECRET_KEY="$SECRET_KEY" \
    -e DATABASE_NAME="$DATABASE_NAME" \
    -e ENVIRONMENT=production \
    -e PORT=8080 \
    xai-backend:latest

echo "애플리케이션 배포 완료!"
