FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY --from=builder /root/.local /home/appuser/.local
COPY main.py .

RUN chown -R appuser:appuser /app

USER appuser

ENV PATH=/home/appuser/.local/bin:$PATH

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8003/health')"

EXPOSE 8003

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
