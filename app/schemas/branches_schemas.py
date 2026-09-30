from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class BranchBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=20, description="كود الفرع (BR-001)")
    name: str = Field(..., min_length=2, max_length=200, description="اسم الفرع")
    name_en: Optional[str] = Field(None, max_length=200)
    city_id: Optional[int] = None
    address: Optional[str] = None
    address_en: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    manager_name: Optional[str] = Field(None, max_length=200)
    manager_phone: Optional[str] = Field(None, max_length=20)
    opened_at: Optional[datetime] = None
    is_active: Optional[bool] = True
    notes: Optional[str] = None


class BranchCreate(BranchBase):
    pass


class BranchUpdate(BaseModel):
    name: Optional[str] = None
    name_en: Optional[str] = None
    city_id: Optional[int] = None
    address: Optional[str] = None
    address_en: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    manager_name: Optional[str] = None
    manager_phone: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class BranchSimple(BaseModel):
    """معلومات مختصرة للاستخدام في علاقات أخرى"""
    id: int
    code: str
    name: str
    name_en: Optional[str] = None

    class Config:
        from_attributes = True


class BranchResponse(BranchBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
