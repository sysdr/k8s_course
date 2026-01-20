FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY tests/ ./tests/

# Default command runs all tests
CMD ["pytest", "tests/", "-v", "--json-report", "--json-report-file=/tmp/test-results.json"]
