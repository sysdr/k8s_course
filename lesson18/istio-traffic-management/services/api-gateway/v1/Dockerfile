FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip uninstall -y prometheus-client 2>/dev/null || true && \
    rm -rf /usr/local/lib/python*/site-packages/prometheus_client* 2>/dev/null || true && \
    find /usr/local/lib/python*/site-packages -name "*prometheus*" -delete 2>/dev/null || true

# Copy application
COPY main.py .
# Remove any Python cache to ensure fresh code
RUN find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && \
    find /app -name "*.pyc" -delete 2>/dev/null || true && \
    find /app -name "*.pyo" -delete 2>/dev/null || true

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Remove Python cache and use -B flag to prevent .pyc creation
CMD ["python", "-B", "-u", "main.py"]
