# ── stage 1: dependency install ────────────────────────────────────────────
FROM python:3.11-slim AS deps
WORKDIR /install
RUN pip install --upgrade pip setuptools wheel
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/deps -r requirements.txt

# ── stage 2: final image ───────────────────────────────────────────────────
FROM python:3.11-slim AS runtime
# non-root user for pod security
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app
COPY --from=deps /deps /deps
ENV PYTHONPATH=/deps:/app
COPY app/ ./app/
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s CMD curl -sf http://localhost:8000/health || exit 1
ENTRYPOINT ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
