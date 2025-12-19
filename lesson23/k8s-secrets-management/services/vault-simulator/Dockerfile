FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ /app/

# Non-root user
RUN useradd -m -u 1000 vault && chown -R vault:vault /app
USER vault

EXPOSE 8080

CMD ["python", "main.py"]
