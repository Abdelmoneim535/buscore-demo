from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class BusBase(BaseModel):
    plate_number: str
    model: str
    total_seats: int
    year: Optional[int] = None
    color: Optional[str] = None
    color_en: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    is_active: bool = True


class BusCreate(BusBase):
    pass


class BusResponse(BusBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True