from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import time
import random
from datetime import datetime
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Payment Gateway", version=os.getenv("VERSION", "v1"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
PAYMENT_COUNT = Counter('payments_processed_total', 'Total payments', ['status', 'version'])
PAYMENT_DURATION = Histogram('payment_duration_seconds', 'Payment processing duration', ['version'])

VERSION = os.getenv("VERSION", "v1")
SUCCESS_RATE = float(os.getenv("SUCCESS_RATE", "0.95"))

class Payment(BaseModel):
    order_id: str
    amount: float
    customer_id: str

class PaymentResponse(BaseModel):
    payment_id: str
    order_id: str
    status: str
    amount: float
    timestamp: str
    version: str

payment_counter = 0

@app.get("/health")
async def health():
    return {"status": "healthy", "version": VERSION}

@app.get("/ready")
async def ready():
    return {"status": "ready", "version": VERSION}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/payments", response_model=PaymentResponse)
async def process_payment(payment: Payment):
    global payment_counter
    start_time = time.time()
    
    try:
        # Simulate payment processing
        time.sleep(random.uniform(0.05, 0.15))
        
        # Simulate success/failure based on configured rate
        success = random.random() < SUCCESS_RATE
        
        payment_counter += 1
        payment_id = f"PAY-{payment_counter:08d}"
        
        status = "success" if success else "failed"
        
        if not success:
            PAYMENT_COUNT.labels(status="failed", version=VERSION).inc()
            raise HTTPException(status_code=402, detail="Payment declined")
        
        response = PaymentResponse(
            payment_id=payment_id,
            order_id=payment.order_id,
            status=status,
            amount=payment.amount,
            timestamp=datetime.utcnow().isoformat(),
            version=VERSION
        )
        
        PAYMENT_COUNT.labels(status="success", version=VERSION).inc()
        duration = time.time() - start_time
        PAYMENT_DURATION.labels(version=VERSION).observe(duration)
        
        logger.info(f"Payment processed: {payment_id} - Amount: ${payment.amount:.2f} - Status: {status}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment processing failed: {e}")
        PAYMENT_COUNT.labels(status="error", version=VERSION).inc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/version")
async def version():
    return {
        "service": "payment-gateway",
        "version": VERSION,
        "success_rate": SUCCESS_RATE
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
