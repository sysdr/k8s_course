from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
from datetime import datetime
import uuid
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Payment Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Payment(BaseModel):
    id: str
    order_id: str
    user_id: str
    amount: float = Field(gt=0)
    status: str  # pending, completed, failed
    created_at: str
    completed_at: Optional[str] = None

class CreatePaymentRequest(BaseModel):
    order_id: str
    user_id: str
    amount: float = Field(gt=0)

# In-memory payment storage
payments_db = {}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/ready")
async def readiness_check():
    return {"status": "ready", "payments_count": len(payments_db)}

@app.get("/api/v1/payments", response_model=List[Payment])
async def list_payments(user_id: Optional[str] = None):
    """List all payments or filter by user"""
    payments = list(payments_db.values())
    
    if user_id:
        payments = [p for p in payments if p.user_id == user_id]
    
    return payments

@app.get("/api/v1/payments/{payment_id}", response_model=Payment)
async def get_payment(payment_id: str):
    """Get payment by ID"""
    if payment_id not in payments_db:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return payments_db[payment_id]

@app.post("/api/v1/payments", response_model=Payment, status_code=201)
async def create_payment(request: CreatePaymentRequest):
    """Process payment for order"""
    payment_id = str(uuid.uuid4())
    
    # Simulate payment processing (would integrate with Stripe/PayPal in production)
    # Randomly fail 2% of payments for testing
    if random.random() < 0.02:
        payment = Payment(
            id=payment_id,
            order_id=request.order_id,
            user_id=request.user_id,
            amount=request.amount,
            status="failed",
            created_at=datetime.utcnow().isoformat()
        )
        payments_db[payment_id] = payment
        logger.warning(f"Payment {payment_id} failed")
        raise HTTPException(status_code=400, detail="Payment processing failed")
    
    payment = Payment(
        id=payment_id,
        order_id=request.order_id,
        user_id=request.user_id,
        amount=request.amount,
        status="completed",
        created_at=datetime.utcnow().isoformat(),
        completed_at=datetime.utcnow().isoformat()
    )
    
    payments_db[payment_id] = payment
    logger.info(f"Payment {payment_id} completed for order {request.order_id}")
    
    return payment

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
