# 매우 간단한 Dockerfile - Cloud Run 실험용
FROM python:3.11-slim

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 직접 설치 (uv 없이)
RUN pip install fastapi uvicorn[standard] python-multipart

# 애플리케이션 코드 복사
COPY main.py ./

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# 포트 노출
EXPOSE 8080

# 애플리케이션 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]