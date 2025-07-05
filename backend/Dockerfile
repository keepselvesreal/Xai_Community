# UV 기반 FastAPI 컨테이너
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필수 도구 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# UV 설치
RUN pip install uv

# 프로젝트 의존성 파일 복사
COPY pyproject.toml uv.lock ./

# 의존성 설치 (lockfile 기반)
RUN uv sync --frozen

# 소스 코드 복사
COPY . .

# 업로드 디렉토리 생성
RUN mkdir -p uploads

# 포트 설정
EXPOSE 8000

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# 애플리케이션 시작
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]