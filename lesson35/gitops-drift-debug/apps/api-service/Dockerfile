FROM python:3.11-slim as builder

WORKDIR /app

RUN pip install --no-cache-dir poetry==1.7.1

COPY pyproject.toml ./
RUN poetry config virtualenvs.create false \
    && poetry lock --no-update || true \
    && poetry install --only main --no-interaction --no-ansi

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY src/ ./src/

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
