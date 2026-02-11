import logging
import json
from collections import defaultdict, deque
from kafka import KafkaConsumer
from prometheus_client import Counter, Gauge, start_http_server
import os

logging.basicConfig(level=logging.INFO)

LOGS_ANALYZED = Counter("log_analyzer_analyzed_total", "Analyzed", ["service"])
ERROR_RATE = Gauge("log_analyzer_error_rate", "Error rate", ["service"])
ANOMALIES = Counter("log_analyzer_anomalies_total", "Anomalies", ["service", "type"])

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

consumer = KafkaConsumer(
    "transformed-logs",
    bootstrap_servers=KAFKA_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode()),
    group_id="analyzer"
)

windows = defaultdict(lambda: deque(maxlen=100))

logging.info("Analyzer started")
start_http_server(8080)

for msg in consumer:
    try:
        data = msg.value
        svc = data.get("service", "unknown")
        has_error = data.get("has_error", False)
        
        windows[svc].append(has_error)
        window = windows[svc]
        error_rate = sum(window) / len(window) if window else 0
        
        ERROR_RATE.labels(service=svc).set(error_rate)
        LOGS_ANALYZED.labels(service=svc).inc()
        
        if error_rate > 0.1:
            ANOMALIES.labels(service=svc, type="high_error_rate").inc()
            logging.warning(f"High error rate: {svc} = {error_rate:.2%}")
    except Exception as e:
        logging.error(f"Error: {e}")
