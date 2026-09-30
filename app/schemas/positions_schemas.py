from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class PositionBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    name_en: Optional[str] = Field(None, max_length=100)
    category: str = Field("other", description="driver | assistant | admin | other")
    icon: Optional[str] = Field("fa-briefcase", max_length=50)
    sort_order: Optional[int] = 0
    is_active: bool = True


class PositionCreate(PositionBase):
    pass


class PositionResponse(PositionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
