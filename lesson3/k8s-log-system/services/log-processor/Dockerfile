FROM python:3.11-slim as builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

RUN useradd -m -u 1000 appuser

WORKDIR /app
COPY --from=builder /root/.local /home/appuser/.local
COPY app/ .

ENV PATH=/home/appuser/.local/bin:$PATH

USER appuser

EXPOSE 8080

# Graceful shutdown handling
STOPSIGNAL SIGTERM

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
