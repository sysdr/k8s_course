# Example 4: Python FastAPI Application

## Objective
Build a production-ready Python API with multi-stage Docker builds and dependency optimization.

## What You'll Learn
- Multi-stage builds for smaller images
- Running as non-root user for security
- Python dependency caching strategies
- Docker Compose for multi-container apps
- Health checks and monitoring

## Quick Start

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t python-api .
docker run -p 8000:8000 python-api
```

Visit:
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Multi-Stage Build Explained

```dockerfile
# Stage 1: Builder (installs dependencies)
FROM python:3.11-slim as builder
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 2: Production (only runtime needed)
FROM python:3.11-slim
COPY --from=builder /root/.local /home/appuser/.local
```

**Why?** Final image doesn't include pip, build tools, or cached layers from dependency installation. This reduces image size by ~200MB.

## Security Best Practices

1. **Non-root user**: Application runs as `appuser`, not root
2. **Minimal base image**: `python:3.11-slim` instead of full Python image
3. **No cache**: `--no-cache-dir` prevents pip cache bloat
4. **Health checks**: Automated container health monitoring

## Testing the API

```bash
# Create an item
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"id": 1, "name": "Docker Book", "price": 29.99}'

# Get all items
curl http://localhost:8000/items

# Container info
curl http://localhost:8000/container-info
```

## Image Size Comparison

```bash
# Single-stage build: ~1GB
# Multi-stage build: ~150MB

docker images python-api
```

## Production Enhancements

- Add environment-based configuration
- Implement logging to stdout/stderr
- Add Prometheus metrics endpoint
- Configure CORS properly
- Add rate limiting
- Implement authentication
