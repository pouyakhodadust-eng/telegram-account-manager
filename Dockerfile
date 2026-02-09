# Telegram Account Management Bot - Dockerfile
# Multi-stage build for production deployment

# ============================================================================
# Build Stage
# ============================================================================
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ============================================================================
# Production Stage
# ============================================================================
FROM python:3.11-slim-bookworm AS production

WORKDIR /app/src

# Create non-root user
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Copy installed Python packages
COPY --from=builder /install /usr/local

# Copy application code (only src directory to avoid duplication)
COPY --chown=appuser:appgroup src/ ./

# Copy configuration file
COPY --chown=appuser:appgroup config.yaml /app/config.yaml

# Create required directories (mount points for volumes)
RUN mkdir -p /app/data/{sessions,exports,logs} && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Environment variables
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Expose port (for health checks and metrics)
EXPOSE 8080

# Entry point
ENTRYPOINT ["uvicorn", "bot.web:app", "--host", "0.0.0.0", "--port", "8080"]

# ============================================================================
# Development Instructions (run locally, not in Docker)
# ============================================================================
# To run locally for development:
# 1. Create a virtual environment: python -m venv venv
# 2. Activate it: source venv/bin/activate
# 3. Install deps: pip install -r requirements.txt
# 4. Run: python -m bot.main
