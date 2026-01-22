import uuid
import time
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
import structlog
import logging
from contextlib import asynccontextmanager
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
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
ORDER_CREATED = Counter('order_service_orders_created_total', 'Total orders created')
ORDER_VALUE = Histogram('order_service_order_value', 'Order values', buckets=[10, 50, 100, 500, 1000, 5000])
ACTIVE_ORDERS = Gauge('order_service_active_orders', 'Currently active orders')
PROCESSING_DURATION = Histogram('order_service_processing_duration_seconds', 'Order processing duration')

# In-memory store (replace with database in production)
orders_db: Dict[str, dict] = {}

class OrderItem(BaseModel):
    product_id: str
    quantity: int
    price: float

class CreateOrderRequest(BaseModel):
    customer_id: str
    items: List[OrderItem]
    amount: float

class OrderResponse(BaseModel):
    order_id: str
    customer_id: str
    status: str
    amount: float
    created_at: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("order_service_startup", message="Order Service starting")
    yield
    logger.info("order_service_shutdown", message="Order Service shutting down")

app = FastAPI(
    title="Order Service",
    description="Handles order creation and management",
    version="1.0.0",
    lifespan=lifespan
)

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    structlog.contextvars.bind_contextvars(
        correlation_id=correlation_id,
        service="order-service",
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
    return {"status": "healthy", "service": "order-service"}

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/orders", response_model=OrderResponse)
async def create_order(order_request: CreateOrderRequest):
    order_id = f"ORD-{uuid.uuid4().hex[:12].upper()}"
    
    logger.info("order_creation_started",
               order_id=order_id,
               customer_id=order_request.customer_id,
               items_count=len(order_request.items),
               total_amount=order_request.amount)
    
    start_time = time.time()
    
    try:
        # Validate order
        if order_request.amount <= 0:
            logger.warning("invalid_order_amount",
                          order_id=order_id,
                          amount=order_request.amount)
            raise HTTPException(status_code=400, detail="Invalid order amount")
        
        if not order_request.items:
            logger.warning("empty_order_items", order_id=order_id)
            raise HTTPException(status_code=400, detail="Order must contain items")
        
        # Create order
        order = {
            "order_id": order_id,
            "customer_id": order_request.customer_id,
            "items": [item.dict() for item in order_request.items],
            "amount": order_request.amount,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }
        
        orders_db[order_id] = order
        
        # Update metrics
        ORDER_CREATED.inc()
        ORDER_VALUE.observe(order_request.amount)
        ACTIVE_ORDERS.inc()
        
        duration = time.time() - start_time
        PROCESSING_DURATION.observe(duration)
        
        logger.info("order_created_successfully",
                   order_id=order_id,
                   processing_time_ms=round(duration * 1000, 2))
        
        # Log business event
        logger.info("business_event",
                   event_type="order_created",
                   order_id=order_id,
                   customer_id=order_request.customer_id,
                   order_value=order_request.amount,
                   items_count=len(order_request.items))
        
        return OrderResponse(**order)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("order_creation_failed",
                    order_id=order_id,
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Failed to create order")

@app.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str):
    logger.info("order_lookup", order_id=order_id)
    
    if order_id not in orders_db:
        logger.warning("order_not_found", order_id=order_id)
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = orders_db[order_id]
    logger.info("order_retrieved", order_id=order_id, status=order["status"])
    
    return OrderResponse(**order)

@app.put("/orders/{order_id}/status")
async def update_order_status(order_id: str, status: str):
    logger.info("order_status_update",
               order_id=order_id,
               new_status=status)
    
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    old_status = orders_db[order_id]["status"]
    orders_db[order_id]["status"] = status
    
    logger.info("business_event",
               event_type="order_status_changed",
               order_id=order_id,
               old_status=old_status,
               new_status=status)
    
    if status == "completed":
        ACTIVE_ORDERS.dec()
    
    return {"order_id": order_id, "status": status}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
