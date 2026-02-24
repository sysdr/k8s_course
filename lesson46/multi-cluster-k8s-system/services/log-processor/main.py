from fastapi import FastAPI
from kafka import KafkaConsumer, KafkaProducer
import json
import logging
import threading
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Log Processor Service", version="1.0.0")

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
CLUSTER_NAME = os.getenv("CLUSTER_NAME", "unknown")

class LogProcessor:
    def __init__(self):
        self.consumer = KafkaConsumer(
            'raw-logs',
            bootstrap_servers=KAFKA_BOOTSTRAP,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id=f'log-processor-{CLUSTER_NAME}',
            auto_offset_reset='earliest'
        )
        self.producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        self.processed_count = 0
        
    def process_logs(self):
        """Process logs from Kafka"""
        for message in self.consumer:
            try:
                log_data = message.value
                
                # Enrich log data
                enriched_log = {
                    **log_data,
                    'processed_at': datetime.utcnow().isoformat(),
                    'processor_cluster': CLUSTER_NAME,
                    'severity_score': self.calculate_severity(log_data['level'])
                }
                
                # Forward to analytics
                self.producer.send('processed-logs', value=enriched_log)
                self.processed_count += 1
                
                if self.processed_count % 100 == 0:
                    logger.info(f"Processed {self.processed_count} logs in {CLUSTER_NAME}")
                    
            except Exception as e:
                logger.error(f"Error processing log: {str(e)}")
    
    def calculate_severity(self, level: str) -> int:
        severity_map = {
            'DEBUG': 1,
            'INFO': 2,
            'WARNING': 3,
            'ERROR': 4,
            'CRITICAL': 5
        }
        return severity_map.get(level, 0)

processor = LogProcessor()

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting log processor in cluster: {CLUSTER_NAME}")
    processing_thread = threading.Thread(target=processor.process_logs, daemon=True)
    processing_thread.start()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "cluster": CLUSTER_NAME,
        "processed_count": processor.processed_count
    }

@app.get("/metrics")
async def metrics():
    return {
        "log_processor_processed_total": processor.processed_count,
        "cluster": CLUSTER_NAME
    }
