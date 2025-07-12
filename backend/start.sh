#!/bin/bash
# Cloud Run startup script with PORT environment variable support

# Get PORT from environment variable, default to 8080
PORT=${PORT:-8080}

# Start uvicorn with dynamic port
exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1 --log-level info