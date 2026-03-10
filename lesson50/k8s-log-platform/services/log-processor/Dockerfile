FROM python:3.11-slim AS base
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /app

FROM base AS runtime
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -r -u 1001 appuser && chown -R appuser /app
USER appuser
EXPOSE 9090
CMD ["python", "-m", "main"]
