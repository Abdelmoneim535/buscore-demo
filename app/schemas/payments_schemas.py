from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from decimal import Decimal
from enum import Enum

class PaymentMethod(str, Enum):
    BANK = "bank"
    CASH = "cash"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentBase(BaseModel):
    booking_id: int
    amount: Decimal = Field(..., gt=0)
    payment_method: PaymentMethod
    transaction_id: Optional[str] = Field(None, max_length=100)

class PaymentCreate(PaymentBase):
    pass

class PaymentResponse(PaymentBase):
    id: int
    status: PaymentStatus
    paid_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PaymentUpdateStatus(BaseModel):
    status: PaymentStatus
    transaction_id: Optional[str] = None