FROM python:3.11-slim AS deps
WORKDIR /install
RUN pip install --upgrade pip setuptools wheel
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/deps -r requirements.txt

FROM python:3.11-slim AS runtime
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app
COPY --from=deps /deps /deps
ENV PYTHONPATH=/deps:/app
COPY app/ ./app/
USER appuser
EXPOSE 8001
HEALTHCHECK --interval=10s --timeout=3s CMD curl -sf http://localhost:8001/health || exit 1
ENTRYPOINT ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
