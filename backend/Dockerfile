# Python base image - optimized for Cloud Run
FROM python:3.11-slim

# Install system dependencies (curl for health check)
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
COPY README.md ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Environment file will be set via Cloud Run environment variables
# No need to copy .env.prod - using Cloud Run env vars instead

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser -m

# Create uploads directory and set permissions  
RUN mkdir -p uploads && chown -R appuser:appuser /app

# Create UV cache directory and set permissions
RUN mkdir -p /home/appuser/.cache/uv && chown -R appuser:appuser /home/appuser/.cache

# Switch to non-root user
USER appuser

# Cloud Run optimized environment variables
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ENVIRONMENT=production

# Expose port
EXPOSE 8080

# Health check for Cloud Run
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Start application with uv run - use PORT environment variable for Cloud Run
CMD ["sh", "-c", "uv run uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1 --log-level info"]