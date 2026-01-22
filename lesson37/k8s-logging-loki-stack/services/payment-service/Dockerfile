FROM python:3.11-slim as builder

WORKDIR /build
COPY app/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /root/.local /home/appuser/.local
COPY app/ .

RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH
USER appuser

EXPOSE 8002

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
