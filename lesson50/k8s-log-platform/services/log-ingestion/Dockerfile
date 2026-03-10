FROM python:3.11-slim AS base
RUN apt-get update && apt-get install -y --no-install-recommends gcc libsnappy-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /app

FROM base AS runtime
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -r -u 1001 appuser && chown -R appuser /app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--loop", "uvloop"]
