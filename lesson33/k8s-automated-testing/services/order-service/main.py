from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import httpx
import logging
from datetime import datetime
import os
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Order Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8000")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8000")

# Models
class OrderItem(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)
    price: float

class Order(BaseModel):
    id: str
    user_id: str
    items: List[OrderItem]
    total_amount: float
    status: str  # pending, confirmed, failed
    created_at: str
    payment_id: Optional[str] = None

class CreateOrderRequest(BaseModel):
    user_id: str
    items: List[dict]  # [{product_id, quantity}]

# In-memory order storage
orders_db = {}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/ready")
async def readiness_check():
    # Check if dependent services are reachable
    try:
        async with httpx.AsyncClient() as client:
            await client.get(f"{PRODUCT_SERVICE_URL}/health", timeout=2.0)
            await client.get(f"{PAYMENT_SERVICE_URL}/health", timeout=2.0)
        return {"status": "ready", "dependencies": "healthy"}
    except Exception as e:
        logger.error(f"Dependency check failed: {e}")
        raise HTTPException(status_code=503, detail="Dependencies not ready")

@app.get("/api/v1/orders", response_model=List[Order])
async def list_orders(user_id: Optional[str] = None):
    """List all orders or filter by user"""
    orders = list(orders_db.values())
    
    if user_id:
        orders = [o for o in orders if o.user_id == user_id]
    
    return orders

@app.get("/api/v1/orders/{order_id}", response_model=Order)
async def get_order(order_id: str):
    """Get order by ID"""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return orders_db[order_id]

@app.post("/api/v1/orders", response_model=Order, status_code=201)
async def create_order(request: CreateOrderRequest):
    """Create new order with product reservation and payment processing"""
    order_id = str(uuid.uuid4())
    order_items = []
    total_amount = 0.0
    
    async with httpx.AsyncClient() as client:
        # Fetch product details and reserve stock
        for item in request.items:
            product_id = item["product_id"]
            quantity = item["quantity"]
            
            # Get product details
            try:
                response = await client.get(f"{PRODUCT_SERVICE_URL}/api/v1/products/{product_id}")
                response.raise_for_status()
                product = response.json()
            except httpx.HTTPError as e:
                raise HTTPException(status_code=400, detail=f"Product {product_id} not found")
            
            # Reserve stock
            try:
                reserve_response = await client.post(
                    f"{PRODUCT_SERVICE_URL}/api/v1/products/{product_id}/reserve",
                    json={"quantity": quantity}
                )
                reserve_response.raise_for_status()
            except httpx.HTTPError as e:
                raise HTTPException(status_code=400, detail=f"Stock reservation failed: {e}")
            
            item_total = product["price"] * quantity
            order_items.append(OrderItem(
                product_id=product_id,
                quantity=quantity,
                price=product["price"]
            ))
            total_amount += item_total
        
        # Process payment
        try:
            payment_response = await client.post(
                f"{PAYMENT_SERVICE_URL}/api/v1/payments",
                json={
                    "order_id": order_id,
                    "amount": total_amount,
                    "user_id": request.user_id
                }
            )
            payment_response.raise_for_status()
            payment_data = payment_response.json()
            payment_id = payment_data["id"]
            
        except httpx.HTTPError as e:
            logger.error(f"Payment processing failed: {e}")
            # In production, would rollback stock reservation here
            raise HTTPException(status_code=400, detail="Payment processing failed")
    
    # Create order
    order = Order(
        id=order_id,
        user_id=request.user_id,
        items=order_items,
        total_amount=total_amount,
        status="confirmed",
        created_at=datetime.utcnow().isoformat(),
        payment_id=payment_id
    )
    
    orders_db[order_id] = order
    logger.info(f"Created order {order_id} for user {request.user_id}")
    
    return order

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
