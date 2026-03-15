# Qubot Backend API Dockerfile
# Multi-stage build for production

# ===========================================
# Stage 1: Builder
# ===========================================
FROM python:3.12-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ===========================================
# Stage 2: Production
# ===========================================
FROM python:3.12-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_HOME=/app \
    PYTHONPATH=/app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create app user
RUN groupadd -r qubot && useradd -r -g qubot qubot

# Set work directory
WORKDIR $APP_HOME

# Copy application code
COPY --chown=qubot:qubot app/ ./app/
COPY --chown=qubot:qubot scripts/ ./scripts/
COPY --chown=qubot:qubot alembic/ ./alembic/
COPY --chown=qubot:qubot alembic.ini .

# Create data directory
RUN mkdir -p /app/data && chown -R qubot:qubot /app

# Switch to non-root user
USER qubot

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/ready || exit 1

# Expose port
EXPOSE 8000

# Run migrations and start server
CMD ["sh", "-c", "python -m alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --loop uvloop --http httptools"]
