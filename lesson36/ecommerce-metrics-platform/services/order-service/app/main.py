from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import CollectorRegistry
from pydantic import BaseModel, Field
from typing import List, Optional
import asyncio
import uvicorn
import logging
import time
import random
from datetime import datetime
from fastapi import Response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
registry = CollectorRegistry()

orders_total = Counter(
    'orders_total',
    'Total number of orders received',
    ['status', 'payment_method'],
    registry=registry
)

order_processing_duration = Histogram(
    'order_processing_duration_seconds',
    'Time spent processing orders',
    ['endpoint'],
    registry=registry,
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

order_value_total = Counter(
    'order_value_total_dollars',
    'Total order value in dollars',
    ['product_category'],
    registry=registry
)

active_orders = Gauge(
    'active_orders_current',
    'Number of currently processing orders',
    registry=registry
)

order_queue_depth = Gauge(
    'order_queue_depth',
    'Number of orders waiting in queue',
    registry=registry
)

# Application
app = FastAPI(title="Order Service", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class OrderItem(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)
    category: str = "general"

class Order(BaseModel):
    customer_id: str
    items: List[OrderItem]
    payment_method: str = "credit_card"
    priority: str = "standard"

class OrderResponse(BaseModel):
    order_id: str
    status: str
    total_amount: float
    estimated_delivery: str
    processing_time: float

# In-memory order queue
order_queue: List[dict] = []

# Background processor
async def process_order_background(order_data: dict):
    """Simulate order processing with realistic delays"""
    order_id = order_data['order_id']
    active_orders.inc()
    
    try:
        # Simulate payment processing (200-800ms)
        await asyncio.sleep(random.uniform(0.2, 0.8))
        
        # Simulate inventory check (100-300ms)
        await asyncio.sleep(random.uniform(0.1, 0.3))
        
        # Simulate shipping calculation (50-150ms)
        await asyncio.sleep(random.uniform(0.05, 0.15))
        
        # Mark order as processed
        order_data['status'] = 'completed'
        orders_total.labels(status='completed', payment_method=order_data['payment_method']).inc()
        
        logger.info(f"Order {order_id} completed successfully")
        
    except Exception as e:
        order_data['status'] = 'failed'
        orders_total.labels(status='failed', payment_method=order_data['payment_method']).inc()
        logger.error(f"Order {order_id} failed: {str(e)}")
    
    finally:
        active_orders.dec()
        order_queue_depth.set(len(order_queue))

@app.post("/api/orders", response_model=OrderResponse)
async def create_order(order: Order, background_tasks: BackgroundTasks):
    """Create new order with metrics tracking"""
    start_time = time.time()
    
    try:
        # Generate order ID
        order_id = f"ORD-{int(time.time() * 1000)}-{random.randint(1000, 9999)}"
        
        # Calculate total
        total_amount = sum(item.price * item.quantity for item in order.items)
        
        # Track order value by category
        for item in order.items:
            order_value_total.labels(product_category=item.category).inc(item.price * item.quantity)
        
        # Add to processing queue
        order_data = {
            'order_id': order_id,
            'customer_id': order.customer_id,
            'total_amount': total_amount,
            'payment_method': order.payment_method,
            'status': 'processing',
            'created_at': datetime.utcnow().isoformat()
        }
        
        order_queue.append(order_data)
        order_queue_depth.set(len(order_queue))
        
        # Start background processing
        background_tasks.add_task(process_order_background, order_data)
        
        # Record initial order
        orders_total.labels(status='received', payment_method=order.payment_method).inc()
        
        processing_time = time.time() - start_time
        order_processing_duration.labels(endpoint='create_order').observe(processing_time)
        
        return OrderResponse(
            order_id=order_id,
            status='processing',
            total_amount=total_amount,
            estimated_delivery='2-3 business days',
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Order creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Order processing failed")

@app.get("/api/orders/{order_id}")
async def get_order(order_id: str):
    """Get order status"""
    order = next((o for o in order_queue if o['order_id'] == order_id), None)
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order

@app.get("/api/orders")
async def list_orders(limit: int = 50):
    """List recent orders"""
    return order_queue[-limit:]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "order-service",
        "timestamp": datetime.utcnow().isoformat(),
        "active_orders": active_orders._value.get(),
        "queue_depth": len(order_queue)
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    if len(order_queue) > 1000:
        raise HTTPException(status_code=503, detail="Queue overloaded")
    
    return {"status": "ready"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)

@app.get("/api/metrics")
async def metrics_json():
    """JSON metrics endpoint for dashboard"""
    import json
    from prometheus_client import generate_latest
    
    # Get metrics as text and parse
    metrics_text = generate_latest(registry).decode('utf-8')
    metrics_dict = {}
    
    for line in metrics_text.split('\n'):
        if line.startswith('#') or not line.strip():
            continue
        # Parse Prometheus format: metric_name{labels} value
        match = line.split()
        if len(match) >= 2:
            metric_name = match[0].split('{')[0]
            try:
                value = float(match[-1])
                metrics_dict[metric_name] = value
            except (ValueError, IndexError):
                pass
    
    # Get current gauge values
    metrics_dict['active_orders'] = active_orders._value.get()
    metrics_dict['queue_depth'] = len(order_queue)
    
    # Calculate rates (simplified - in production use PromQL)
    total_orders = sum(1 for _ in order_queue if 'status' in _ and _['status'] == 'completed')
    failed_orders = sum(1 for _ in order_queue if 'status' in _ and _['status'] == 'failed')
    
    return {
        "active_orders": metrics_dict.get('active_orders', 0),
        "queue_depth": metrics_dict.get('queue_depth', 0),
        "total_orders": len(order_queue),
        "completed_orders": total_orders,
        "failed_orders": failed_orders,
        "processing_orders": active_orders._value.get(),
        "timestamp": datetime.utcnow().isoformat()
    }

# Generate load for testing
@app.post("/api/load-test/start")
async def start_load_test(background_tasks: BackgroundTasks):
    """Generate synthetic load for testing autoscaling"""
    
    async def generate_load():
        for i in range(100):
            try:
                order = Order(
                    customer_id=f"TEST-{random.randint(1000, 9999)}",
                    items=[
                        OrderItem(
                            product_id=f"PROD-{random.randint(100, 999)}",
                            quantity=random.randint(1, 5),
                            price=random.uniform(10.0, 500.0),
                            category=random.choice(['electronics', 'clothing', 'books', 'food'])
                        )
                    ],
                    payment_method=random.choice(['credit_card', 'debit_card', 'paypal'])
                )
                
                await create_order(order, background_tasks)
                await asyncio.sleep(random.uniform(0.01, 0.1))
                
            except Exception as e:
                logger.error(f"Load test error: {str(e)}")
    
    background_tasks.add_task(generate_load)
    return {"status": "load test started", "orders": 100}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
