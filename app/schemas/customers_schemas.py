from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from decimal import Decimal


class CustomerBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200, description="الاسم الكامل")
    phone: str = Field(..., min_length=10, max_length=20, description="رقم الهاتف الأساسي")
    phone_secondary: Optional[str] = Field(None, max_length=20, description="رقم هاتف ثانوي")
    email: Optional[str] = Field(None, max_length=100)
    id_number: Optional[str] = Field(None, max_length=50)
    passport_number: Optional[str] = Field(None, max_length=50, description="رقم الجواز")
    national_id: Optional[str] = Field(None, max_length=50, description="الرقم الوطني")
    birth_date: Optional[datetime] = None
    nationality: Optional[str] = Field(None, max_length=50)
    preferred_branch_id: Optional[int] = None
    is_vip: Optional[bool] = False
    is_active: Optional[bool] = True
    notes: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    phone_secondary: Optional[str] = None
    email: Optional[str] = None
    id_number: Optional[str] = None
    passport_number: Optional[str] = None
    national_id: Optional[str] = None
    birth_date: Optional[datetime] = None
    nationality: Optional[str] = None
    preferred_branch_id: Optional[int] = None
    is_vip: Optional[bool] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class CustomerResponse(CustomerBase):
    id: int
    customer_code: Optional[str] = None
    total_bookings: int = 0
    total_tickets: int = 0
    total_infants: int = 0
    total_spent: Decimal = Decimal("0")
    created_at: datetime
    last_booking_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CustomerSimple(BaseModel):
    """معلومات مختصرة للاستخدام في علاقات أخرى"""
    id: int
    full_name: str
    phone: str
    is_vip: bool = False

    class Config:
        from_attributes = True
