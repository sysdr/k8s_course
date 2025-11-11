FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
RUN useradd -m -u 1000 appuser
COPY --from=builder /root/.local /home/appuser/.local
COPY worker.py .
RUN chown -R appuser:appuser /app /home/appuser/.local
USER appuser
ENV PATH=/home/appuser/.local/bin:$PATH
CMD ["python", "worker.py"]
