from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx
import os
import time
import random
from datetime import datetime
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Order Service", version=os.getenv("VERSION", "v1"))

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
REQUEST_COUNT = Counter('order_service_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('order_service_request_duration_seconds', 'Request duration', ['method', 'endpoint'])
ORDER_TOTAL = Counter('orders_created_total', 'Total orders created', ['version'])
PAYMENT_FAILURES = Counter('payment_failures_total', 'Payment failures', ['version'])

# Configuration
VERSION = os.getenv("VERSION", "v1")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment-gateway:8080")
FAILURE_RATE = float(os.getenv("FAILURE_RATE", "0.0"))
LATENCY_MS = int(os.getenv("LATENCY_MS", "0"))

# Models
class OrderItem(BaseModel):
    product_id: str
    quantity: int
    price: float

class Order(BaseModel):
    customer_id: str
    items: List[OrderItem]
    
class OrderResponse(BaseModel):
    order_id: str
    customer_id: str
    total: float
    status: str
    version: str
    timestamp: str

# In-memory storage
orders = []
order_counter = 0

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "version": VERSION}

@app.get("/ready")
async def ready():
    """Readiness check - validates payment service connectivity"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{PAYMENT_SERVICE_URL}/health", timeout=2.0)
            if response.status_code == 200:
                return {"status": "ready", "version": VERSION}
    except Exception as e:
        logger.error(f"Payment service not ready: {e}")
        raise HTTPException(status_code=503, detail="Payment service unavailable")

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/orders", response_model=OrderResponse)
async def create_order(order: Order, request: Request):
    """Create new order with payment processing"""
    global order_counter
    start_time = time.time()
    
    try:
        # Simulate configurable latency (for canary testing)
        if LATENCY_MS > 0:
            await asyncio.sleep(LATENCY_MS / 1000.0)
        
        # Simulate configurable failure rate (for canary testing)
        if random.random() < FAILURE_RATE:
            REQUEST_COUNT.labels(method="POST", endpoint="/orders", status="500").inc()
            raise HTTPException(status_code=500, detail="Simulated failure")
        
        # Calculate total
        total = sum(item.quantity * item.price for item in order.items)
        
        # Process payment
        order_counter += 1
        order_id = f"ORD-{order_counter:06d}"
        
        async with httpx.AsyncClient() as client:
            payment_response = await client.post(
                f"{PAYMENT_SERVICE_URL}/payments",
                json={
                    "order_id": order_id,
                    "amount": total,
                    "customer_id": order.customer_id
                },
                timeout=5.0
            )
            
            if payment_response.status_code != 200:
                PAYMENT_FAILURES.labels(version=VERSION).inc()
                raise HTTPException(status_code=402, detail="Payment failed")
        
        # Create order response
        order_response = OrderResponse(
            order_id=order_id,
            customer_id=order.customer_id,
            total=total,
            status="completed",
            version=VERSION,
            timestamp=datetime.utcnow().isoformat()
        )
        
        orders.append(order_response.dict())
        
        # Metrics
        ORDER_TOTAL.labels(version=VERSION).inc()
        REQUEST_COUNT.labels(method="POST", endpoint="/orders", status="200").inc()
        duration = time.time() - start_time
        REQUEST_DURATION.labels(method="POST", endpoint="/orders").observe(duration)
        
        logger.info(f"Order created: {order_id} - Total: ${total:.2f} - Version: {VERSION}")
        
        return order_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Order creation failed: {e}")
        REQUEST_COUNT.labels(method="POST", endpoint="/orders", status="500").inc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/orders", response_model=List[OrderResponse])
async def get_orders(limit: int = 100):
    """Get recent orders"""
    REQUEST_COUNT.labels(method="GET", endpoint="/orders", status="200").inc()
    return orders[-limit:]

@app.get("/version")
async def version():
    """Get service version"""
    return {
        "service": "order-service",
        "version": VERSION,
        "failure_rate": FAILURE_RATE,
        "latency_ms": LATENCY_MS
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
