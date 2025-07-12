# Multi-stage build for uv and Cloud Run optimization
FROM python:3.11-slim AS base

# Install system dependencies (curl for health check)
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Builder stage
FROM base AS builder

# Copy uv binary from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# uv environment variables for optimization
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

# Copy dependency files first for Docker layer caching
COPY pyproject.toml uv.lock ./
COPY README.md ./

# Install dependencies (Cloud Build compatible - no cache mount)
RUN uv sync --frozen --no-install-project --no-dev --verbose

# Copy application code
COPY . .

# Install project itself
RUN uv sync --frozen --no-dev --verbose

# Production stage
FROM base

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser -m

# Copy application and virtual environment from builder
COPY --from=builder --chown=appuser:appuser /app /app

# Create uploads directory
RUN mkdir -p /app/uploads && chown -R appuser:appuser /app/uploads

# Switch to non-root user
USER appuser

WORKDIR /app

# Cloud Run optimized environment variables
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ENVIRONMENT=production
ENV PATH="/app/.venv/bin:$PATH"

# Expose port
EXPOSE 8080

# Health check for Cloud Run
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Set executable permission for startup script
RUN chmod +x /app/start.sh

# Start application with Cloud Run compatible command
CMD ["/app/start.sh"]