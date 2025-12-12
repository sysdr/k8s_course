FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim

# Create non-root user with specific UID (Restricted policy requirement)
RUN groupadd -r processor && useradd -r -g processor -u 10001 processor

WORKDIR /app

COPY --from=builder /root/.local /home/processor/.local
COPY app.py .

# Create tmp directory for writes (Restricted policy: read-only root filesystem)
RUN mkdir -p /tmp/app-data && chown processor:processor /tmp/app-data

# Set ownership of application directory
RUN chown -R processor:processor /app

# Switch to non-root user (Restricted policy requirement)
USER processor

ENV PATH=/home/processor/.local/bin:$PATH

EXPOSE 8001

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
