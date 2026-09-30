from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from enum import Enum

class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class BookingType(str, Enum):
    ONLINE = "online"
    OFFICE = "office"

# ---------- Schemas للركاب ----------
class PassengerBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200, description="الاسم الكامل")
    phone: str = Field(..., min_length=10, max_length=20, description="رقم الهاتف")
    email: Optional[str] = Field(None, max_length=100)
    id_number: Optional[str] = Field(None, max_length=50, description="رقم الإثبات")
    age: Optional[int] = Field(None, ge=0, le=120, description="العمر بالسنة")
    is_infant: Optional[bool] = Field(False, description="هل هو رضيع (أقل من سنتين)؟")
    customer_id: Optional[int] = None
    is_primary: Optional[bool] = False

class PassengerCreate(PassengerBase):
    pass

class PassengerResponse(PassengerBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class PassengerCreate(PassengerBase):
    pass

class PassengerResponse(PassengerBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# ---------- Schemas للأمتعة ----------
class LuggageBase(BaseModel):
    luggage_type: str = Field(..., description="نوع الأمتعة: free, small, medium, large, extra")
    weight_kg: int = Field(..., gt=0, description="الوزن بالكيلوغرام")
    price: Decimal = Field(..., ge=0, description="السعر (0 للمجانية)")
    is_free: bool = Field(False, description="هل هي شنطة مجانية؟")
    quantity: int = Field(1, ge=1, description="العدد")

class LuggageCreate(LuggageBase):
    pass

class LuggageResponse(LuggageBase):
    id: int
    quantity: Optional[int] = 1
    created_at: datetime

    class Config:
        from_attributes = True

# ---------- Schemas للحجوزات ----------
class BookingBase(BaseModel):
    trip_id: int
    passenger_id: int
    seat_numbers: List[int] = Field(default_factory=list)  # ✅ السماح بمصفوفة فارغة
    infant_count: Optional[int] = Field(0, ge=0, le=5)
    booking_type: BookingType
    luggage_ids: Optional[List[int]] = []

class BookingCreate(BookingBase):
    pass

class BookingResponse(BaseModel):
    id: int
    booking_reference: str
    pnr_reference: Optional[str] = None
    ticket_number: Optional[str] = None
    trip_id: int
    passenger: PassengerResponse
    seat_numbers: List[int] = []
    infant_count: Optional[int] = 0
    luggage_items: List[LuggageResponse] = []
    booking_type: BookingType
    status: BookingStatus
    total_price: Decimal
    booked_at: datetime
    #  الفروع والحجز الذاتي
    branch_id: Optional[int] = None
    customer_id: Optional[int] = None
    booking_source: Optional[str] = None
    booking_channel: Optional[str] = None

    class Config:
        from_attributes = True

class BookingUpdateStatus(BaseModel):
    status: BookingStatus

class BookingCreate(BookingBase):
    pass

class BookingResponse(BaseModel):
    id: int
    booking_reference: str
    pnr_reference: Optional[str] = None
    ticket_number: Optional[str] = None
    trip_id: int
    passenger: PassengerResponse
    seat_numbers: List[int]
    infant_count: Optional[int] = 0
    luggage_items: List[LuggageResponse]
    booking_type: BookingType
    status: BookingStatus
    total_price: Decimal
    booked_at: datetime
    #  الفروع والحجز الذاتي
    branch_id: Optional[int] = None
    customer_id: Optional[int] = None
    booking_source: Optional[str] = None
    booking_channel: Optional[str] = None

    class Config:
        from_attributes = True

class BookingUpdateStatus(BaseModel):
    status: BookingStatus

# ============================================================
# Group Booking (الحجز الجماعي - PNR)
# ============================================================

class GroupBookingItem(BaseModel):
    """راكب واحد في المجموعة"""
    passenger_id: int
    seat_numbers: List[int] = []  # فارغة للأطفال الرضع
    luggage_ids: Optional[List[int]] = []


class GroupBookingCreate(BaseModel):
    """إنشاء مجموعة حجز واحدة (عائلة)"""
    trip_id: int
    items: List[GroupBookingItem]
    booking_type: BookingType
    contact_phone: Optional[str] = None  # هاتف التواصل للعائلة
    contact_name: Optional[str] = None   # اسم الشخص المسؤول


class GroupBookingResponse(BaseModel):
    """الرد بعد إنشاء حجز جماعي"""
    pnr_reference: str
    total_price: Decimal
    bookings_count: int
    bookings: List[BookingResponse] = []


# ============================================================
# نهاية Group Booking
# ============================================================
