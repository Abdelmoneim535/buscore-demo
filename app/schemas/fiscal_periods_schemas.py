# -*- coding: utf-8 -*-
"""Schemas: الفترات المحاسبية"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class FiscalPeriodBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    name_en: Optional[str] = None
    period_type: str = "monthly"  # monthly / quarterly / yearly
    start_date: datetime
    end_date: datetime
    status: str = "open"
    notes: Optional[str] = None


class FiscalPeriodCreate(FiscalPeriodBase):
    pass


class FiscalPeriodUpdate(BaseModel):
    name: Optional[str] = None
    name_en: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class FiscalPeriodResponse(FiscalPeriodBase):
    id: int
    closed_by: Optional[int] = None
    closed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
