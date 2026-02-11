import logging
import json
import time
from kafka import KafkaConsumer, KafkaProducer
from prometheus_client import Counter, start_http_server
import os

logging.basicConfig(level=logging.INFO)

MESSAGES_PROCESSED = Counter("log_transformer_processed_total", "Processed", ["status"])
KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

consumer = KafkaConsumer(
    "raw-logs",
    bootstrap_servers=KAFKA_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode()),
    group_id="transformer"
)

producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode()
)

logging.info("Transformer started")

for msg in consumer:
    try:
        data = msg.value
        data["processed_at"] = int(time.time() * 1000)
        data["has_error"] = data.get("level") == "ERROR"
        producer.send("transformed-logs", data)
        MESSAGES_PROCESSED.labels("success").inc()
    except Exception as e:
        MESSAGES_PROCESSED.labels("error").inc()
        logging.error(f"Error: {e}")

start_http_server(8080)
