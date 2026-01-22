import uuid
import time
import random
from datetime import datetime
from typing import Dict
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import structlog
import logging
from contextlib import asynccontextmanager
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()

# Prometheus metrics
PAYMENT_PROCESSED = Counter('payment_service_payments_processed_total', 'Total payments processed', ['status'])
PAYMENT_AMOUNT = Histogram('payment_service_payment_amount', 'Payment amounts', buckets=[10, 50, 100, 500, 1000, 5000])
PAYMENT_DURATION = Histogram('payment_service_processing_duration_seconds', 'Payment processing duration')

# In-memory payment records
payments_db: Dict[str, dict] = {}

class PaymentRequest(BaseModel):
    order_id: str
    amount: float
    payment_method: str = "credit_card"

class PaymentResponse(BaseModel):
    payment_id: str
    order_id: str
    amount: float
    status: str
    transaction_id: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("payment_service_startup", message="Payment Service starting")
    yield
    logger.info("payment_service_shutdown", message="Payment Service shutting down")

app = FastAPI(
    title="Payment Service",
    description="Handles payment processing with audit logging",
    version="1.0.0",
    lifespan=lifespan
)

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    structlog.contextvars.bind_contextvars(
        correlation_id=correlation_id,
        service="payment-service",
        path=request.url.path
    )
    
    start_time = time.time()
    logger.info("request_received", method=request.method)
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        logger.info("request_completed",
                   status_code=response.status_code,
                   duration_ms=round(duration * 1000, 2))
        return response
    except Exception as e:
        logger.error("request_failed", error=str(e))
        raise

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "payment-service"}

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

def mask_sensitive_data(data: str) -> str:
    """Mask sensitive payment data for logging"""
    if len(data) <= 4:
        return "****"
    return f"****{data[-4:]}"

@app.post("/payments", response_model=PaymentResponse)
async def process_payment(payment_request: PaymentRequest):
    payment_id = f"PAY-{uuid.uuid4().hex[:12].upper()}"
    transaction_id = f"TXN-{uuid.uuid4().hex[:16].upper()}"
    
    # Audit log - compliance requirement
    logger.info("payment_processing_initiated",
               payment_id=payment_id,
               order_id=payment_request.order_id,
               amount=payment_request.amount,
               payment_method=payment_request.payment_method,
               log_type="audit")
    
    start_time = time.time()
    
    try:
        # Validate payment
        if payment_request.amount <= 0:
            logger.warning("invalid_payment_amount",
                          payment_id=payment_id,
                          amount=payment_request.amount,
                          log_type="security")
            raise HTTPException(status_code=400, detail="Invalid payment amount")
        
        # Simulate payment processing
        time.sleep(random.uniform(0.1, 0.3))  # Simulate external payment gateway
        
        # Random payment failure (5% failure rate for demo)
        if random.random() < 0.05:
            logger.error("payment_gateway_declined",
                        payment_id=payment_id,
                        order_id=payment_request.order_id,
                        reason="insufficient_funds",
                        log_type="business")
            
            PAYMENT_PROCESSED.labels(status="declined").inc()
            raise HTTPException(status_code=402, detail="Payment declined")
        
        # Successful payment
        payment = {
            "payment_id": payment_id,
            "order_id": payment_request.order_id,
            "amount": payment_request.amount,
            "payment_method": payment_request.payment_method,
            "transaction_id": transaction_id,
            "status": "completed",
            "processed_at": datetime.utcnow().isoformat()
        }
        
        payments_db[payment_id] = payment
        
        # Update metrics
        PAYMENT_PROCESSED.labels(status="completed").inc()
        PAYMENT_AMOUNT.observe(payment_request.amount)
        
        duration = time.time() - start_time
        PAYMENT_DURATION.observe(duration)
        
        # Audit log - successful payment
        logger.info("payment_completed_successfully",
                   payment_id=payment_id,
                   order_id=payment_request.order_id,
                   amount=payment_request.amount,
                   transaction_id=transaction_id,
                   processing_time_ms=round(duration * 1000, 2),
                   log_type="audit")
        
        # Business event log
        logger.info("business_event",
                   event_type="payment_processed",
                   payment_id=payment_id,
                   order_id=payment_request.order_id,
                   amount=payment_request.amount,
                   payment_method=payment_request.payment_method)
        
        return PaymentResponse(**payment)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("payment_processing_failed",
                    payment_id=payment_id,
                    order_id=payment_request.order_id,
                    error=str(e),
                    error_type=type(e).__name__,
                    log_type="error")
        PAYMENT_PROCESSED.labels(status="failed").inc()
        raise HTTPException(status_code=500, detail="Payment processing failed")

@app.get("/payments/{payment_id}")
async def get_payment(payment_id: str):
    logger.info("payment_lookup",
               payment_id=payment_id,
               log_type="audit")
    
    if payment_id not in payments_db:
        logger.warning("payment_not_found",
                      payment_id=payment_id,
                      log_type="security")
        raise HTTPException(status_code=404, detail="Payment not found")
    
    payment = payments_db[payment_id]
    logger.info("payment_retrieved",
               payment_id=payment_id,
               status=payment["status"])
    
    return payment

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
