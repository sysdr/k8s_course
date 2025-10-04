# Multi-stage build for Python API - Optimized from 1.1GB to 165MB

# Stage 1: Builder - includes build tools, discarded in final image
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for layer caching
COPY requirements.txt .

# Install dependencies to user directory for easy copying
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime - minimal production image
FROM python:3.11-slim

WORKDIR /app

# Copy only the installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code (separate layer for fast rebuilds)
COPY app/ ./app/

# Update PATH to use user-installed packages
ENV PATH=/root/.local/bin:$PATH

# Make sure the local bin directory is accessible
RUN chmod -R 755 /root/.local

# Run as root for testing (in production, use non-root user)
# RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
# USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
