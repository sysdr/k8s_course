FROM python:3.11-slim

RUN useradd -m -u 1001 exporter

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .

RUN chown -R exporter:exporter /app

USER exporter

EXPOSE 8081

CMD ["python", "exporter.py"]
