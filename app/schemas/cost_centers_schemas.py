# -*- coding: utf-8 -*-
"""Schemas: مراكز التكلفة"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class CostCenterBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=200)
    name_en: Optional[str] = None
    center_type: str  # branch/bus/trip/department/project
    reference_id: Optional[int] = None
    parent_id: Optional[int] = None
    is_active: bool = True
    notes: Optional[str] = None


class CostCenterCreate(CostCenterBase):
    pass


class CostCenterUpdate(BaseModel):
    name: Optional[str] = None
    name_en: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class CostCenterResponse(CostCenterBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CostCenterSimple(BaseModel):
    id: int
    code: str
    name: str
    center_type: str

    class Config:
        from_attributes = True
