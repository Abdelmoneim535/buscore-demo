from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

class RouteBase(BaseModel):
    code: str = Field(..., min_length=3, max_length=20)
    departure_station_id: int
    arrival_station_id: int
    distance_km: Optional[int] = None

class RouteCreate(RouteBase):
    pass

class RouteResponse(RouteBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class PricingHistoryBase(BaseModel):
    route_id: int
    price: Decimal
    effective_date: datetime

class PricingHistoryCreate(PricingHistoryBase):
    pass

class PricingHistoryResponse(PricingHistoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class EmployeeMini(BaseModel):
    """معلومات مختصرة عن الموظف (للعرض فقط)"""
    id: int
    full_name: str
    full_name_en: Optional[str] = None
    position: Optional[str] = None
    position_en: Optional[str] = None
    phone: Optional[str] = None

    class Config:
        from_attributes = True


class TripBase(BaseModel):
    route_id: int
    bus_id: int
    departure_time: datetime
    arrival_time: Optional[datetime] = None
    price_at_time: Optional[Decimal] = None
    is_active: bool = True
    driver_id: Optional[int] = None
    assistant_id: Optional[int] = None

class TripCreate(TripBase):
    pass

class TripResponse(TripBase):
    id: int
    created_at: datetime
    available_seats: Optional[int] = None
    bus_number: Optional[str] = None
    total_seats: Optional[int] = None
    branch_id: Optional[int] = None
    is_online_sellable: Optional[bool] = True
    driver: Optional[EmployeeMini] = None
    assistant: Optional[EmployeeMini] = None

    class Config:
        from_attributes = True

# ============================================================
# Driver Availability (فحص توفر السائق)
# ============================================================

class DriverAvailabilityItem(BaseModel):
    """سائق مع حالة توفر"""
    id: int
    full_name: str
    full_name_en: Optional[str] = None
    phone: Optional[str] = None
    is_available: bool = True
    conflict_trip_id: Optional[int] = None
    conflict_time_range: Optional[str] = None  # مثال: "10:00 → 14:00"


class DriverAvailabilityResponse(BaseModel):
    """قائمة الموظفين المتاحين لرحلة معينة (سائقين + مساعدين)"""
    available_drivers: List[DriverAvailabilityItem] = []
    busy_drivers: List[DriverAvailabilityItem] = []
    available_assistants: List[DriverAvailabilityItem] = []
    busy_assistants: List[DriverAvailabilityItem] = []

    # للتوافق مع الإصدار القديم
    @property
    def available(self):
        return self.available_drivers + self.available_assistants

    @property
    def busy(self):
        return self.busy_drivers + self.busy_assistants


# ============================================================
# نهاية Driver Availability
# ============================================================
