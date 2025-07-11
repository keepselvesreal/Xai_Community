.PHONY: help install dev start test test-unit test-integration test-cov lint format format-check clean docker-build-cloud docker-deploy-vm

help:  ## 도움말 표시
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## 의존성 설치
	uv sync

dev:  ## 개발 서버 시작
	PYTHONPATH=$(PWD) uv run python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

start:  ## 프로덕션 서버 시작
	PYTHONPATH=$(PWD) uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000

test:  ## 모든 테스트 실행
	uv run pytest

test-unit:  ## 단위 테스트 실행
	uv run pytest tests/unit -v

test-integration:  ## 통합 테스트 실행
	uv run pytest tests/integration -v

test-cov:  ## 커버리지와 함께 테스트 실행
	uv run pytest --cov=backend --cov-report=html --cov-report=term

lint:  ## 코드 린팅
	uv run flake8 src tests

format:  ## 코드 포맷팅
	uv run black src tests

format-check:  ## 코드 포맷팅 체크
	uv run black --check src tests

clean:  ## 캐시 및 임시 파일 정리
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/ 

docker-build-cloud:  ## Cloud Run용 Docker 이미지 빌드
	cd deploy/cloud-run && docker build -t xai-backend-cloud -f Dockerfile ../..

docker-deploy-vm:  ## VM용 Docker Compose 배포
	cd deploy/vm && docker-compose up -d