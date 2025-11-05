FROM python:3.11-slim as builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

# Create non-root user first
RUN useradd -m -u 1000 appuser

# Copy installed packages from builder to appuser's home
COPY --from=builder /root/.local /home/appuser/.local
RUN chown -R appuser:appuser /home/appuser/.local

COPY app/ ./app/
RUN chown -R appuser:appuser /app

ENV PATH=/home/appuser/.local/bin:$PATH

USER appuser

CMD ["python", "-m", "app.main"]
