FROM python:3.11-slim

WORKDIR /app

# Install diagnostic tools for debugging exercises
RUN apt-get update && apt-get install -y \
    dnsutils \
    curl \
    wget \
    iputils-ping \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=3 \
    CMD wget -qO- http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
