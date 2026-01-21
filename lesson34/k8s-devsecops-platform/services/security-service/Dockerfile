FROM python:3.11-slim AS builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY main.py .

# Security: Run as non-root user
RUN useradd -m -u 1001 appuser && \
    chown -R appuser:appuser /app && \
    mkdir -p /home/appuser/.local && \
    cp -r /root/.local/* /home/appuser/.local/ && \
    chown -R appuser:appuser /home/appuser/.local

USER appuser

# Make sure scripts in .local are usable
ENV PATH=/home/appuser/.local/bin:$PATH

EXPOSE 8004

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
