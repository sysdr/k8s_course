import uuid
import time
import json
from typing import Optional
from datetime import datetime
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import structlog
import logging
from contextlib import asynccontextmanager
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Configure structured logging
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
    cache_logger_on_first_use=False
)

logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter('api_gateway_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('api_gateway_request_duration_seconds', 'Request duration', ['method', 'endpoint'])
ERROR_COUNT = Counter('api_gateway_errors_total', 'Total errors', ['error_type'])

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("api_gateway_startup", message="API Gateway starting up")
    yield
    logger.info("api_gateway_shutdown", message="API Gateway shutting down")

app = FastAPI(
    title="API Gateway",
    description="Production API Gateway with Distributed Logging",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Correlation ID middleware
@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    structlog.contextvars.bind_contextvars(
        correlation_id=correlation_id,
        service="api-gateway",
        path=request.url.path,
        method=request.method
    )
    
    start_time = time.time()
    
    logger.info("request_received",
                client_ip=request.client.host,
                user_agent=request.headers.get("user-agent"))
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        response.headers["X-Correlation-ID"] = correlation_id
        
        logger.info("request_completed",
                   status_code=response.status_code,
                   duration_ms=round(duration * 1000, 2))
        
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error("request_failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    duration_ms=round(duration * 1000, 2))
        ERROR_COUNT.labels(error_type=type(e).__name__).inc()
        raise

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "api-gateway"}

@app.get("/ready")
async def readiness_check():
    # Check downstream services
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            order_health = await client.get("http://order-service:8001/health")
            payment_health = await client.get("http://payment-service:8002/health")
            
        if order_health.status_code == 200 and payment_health.status_code == 200:
            return {"status": "ready"}
        else:
            logger.warning("downstream_service_unhealthy",
                          order_status=order_health.status_code,
                          payment_status=payment_health.status_code)
            raise HTTPException(status_code=503, detail="Downstream services not ready")
    except Exception as e:
        logger.error("readiness_check_failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not ready")

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/api/orders")
async def create_order(request: Request):
    body = await request.json()
    
    logger.info("order_creation_initiated",
               order_value=body.get("amount", 0),
               customer_id=body.get("customer_id"),
               items_count=len(body.get("items", [])))
    
    try:
        # Forward to order service
        async with httpx.AsyncClient(timeout=5.0) as client:
            correlation_id = structlog.contextvars.get_contextvars().get("correlation_id")
            headers = {"X-Correlation-ID": correlation_id}
            
            order_response = await client.post(
                "http://order-service:8001/orders",
                json=body,
                headers=headers
            )
            
            if order_response.status_code != 200:
                logger.error("order_service_error",
                           status_code=order_response.status_code,
                           response=order_response.text)
                raise HTTPException(status_code=order_response.status_code,
                                  detail="Order creation failed")
            
            order_data = order_response.json()
            order_id = order_data.get("order_id")
            
            # Process payment
            payment_payload = {
                "order_id": order_id,
                "amount": body.get("amount"),
                "payment_method": body.get("payment_method", "credit_card")
            }
            
            payment_response = await client.post(
                "http://payment-service:8002/payments",
                json=payment_payload,
                headers=headers
            )
            
            if payment_response.status_code != 200:
                logger.error("payment_service_error",
                           order_id=order_id,
                           status_code=payment_response.status_code)
                # Implement compensation logic here
                raise HTTPException(status_code=payment_response.status_code,
                                  detail="Payment processing failed")
            
            logger.info("order_completed_successfully",
                       order_id=order_id,
                       amount=body.get("amount"))
            
            return {
                "order_id": order_id,
                "status": "completed",
                "message": "Order created and payment processed successfully"
            }
            
    except httpx.TimeoutException:
        logger.error("downstream_timeout", service="order-service")
        ERROR_COUNT.labels(error_type="timeout").inc()
        raise HTTPException(status_code=504, detail="Downstream service timeout")
    except Exception as e:
        logger.error("order_processing_failed",
                    error=str(e),
                    error_type=type(e).__name__)
        ERROR_COUNT.labels(error_type="internal_error").inc()
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/orders/{order_id}")
async def get_order(order_id: str):
    logger.info("order_retrieval_requested", order_id=order_id)
    
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            correlation_id = structlog.contextvars.get_contextvars().get("correlation_id")
            headers = {"X-Correlation-ID": correlation_id}
            
            response = await client.get(
                f"http://order-service:8001/orders/{order_id}",
                headers=headers
            )
            
            if response.status_code == 404:
                logger.warning("order_not_found", order_id=order_id)
                raise HTTPException(status_code=404, detail="Order not found")
            
            return response.json()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("order_retrieval_failed", order_id=order_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve order")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
