FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim
RUN useradd -m -u 1001 appuser
WORKDIR /app
COPY --from=builder /install /usr/local
COPY app/ ./app/
USER appuser
EXPOSE 9090
CMD ["python", "-m", "app.main"]
