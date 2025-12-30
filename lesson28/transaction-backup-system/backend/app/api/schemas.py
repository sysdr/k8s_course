"""Pydantic schemas for API validation"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class TransactionCreate(BaseModel):
    """Schema for creating a new transaction"""
    user_id: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    transaction_type: str = Field(..., pattern="^(payment|refund|transfer)$")
    description: Optional[str] = Field(None, max_length=500)
    
    @validator('currency')
    def validate_currency(cls, v):
        allowed = ['USD', 'EUR', 'GBP', 'JPY']
        if v.upper() not in allowed:
            raise ValueError(f'Currency must be one of {allowed}')
        return v.upper()

class TransactionResponse(BaseModel):
    """Schema for transaction response"""
    id: int
    user_id: str
    amount: float
    currency: str
    transaction_type: str
    description: Optional[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class TransactionStats(BaseModel):
    """Schema for transaction statistics"""
    total_transactions: int
    total_volume: float
    recent_transactions_1h: int
    last_backup_size: int
