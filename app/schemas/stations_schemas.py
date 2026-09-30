from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CityBase(BaseModel):
    name: str
    name_en: Optional[str] = None
    code: str


class CityCreate(CityBase):
    pass


class CityResponse(CityBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class StationBase(BaseModel):
    name: str
    name_en: Optional[str] = None
    city_id: int
    address: Optional[str] = None
    address_en: Optional[str] = None
    phone: Optional[str] = None


class StationCreate(StationBase):
    pass


class StationResponse(StationBase):
    id: int
    created_at: datetime
    city: Optional[CityResponse] = None

    class Config:
        from_attributes = True