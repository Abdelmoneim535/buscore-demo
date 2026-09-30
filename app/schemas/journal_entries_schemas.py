# -*- coding: utf-8 -*-
"""Schemas: دفتر اليومية"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal


class JournalEntryLineBase(BaseModel):
    account_id: int
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    description: Optional[str] = None
    cost_center_id: Optional[int] = None
    line_order: int = 0


class JournalEntryLineCreate(JournalEntryLineBase):
    pass


class JournalEntryLineResponse(JournalEntryLineBase):
    id: int
    entry_id: int

    class Config:
        from_attributes = True


class JournalEntryBase(BaseModel):
    entry_date: datetime
    entry_type: str = "normal"
    description: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    branch_id: Optional[int] = None
    customer_id: Optional[int] = None
    booking_id: Optional[int] = None
    fiscal_period_id: Optional[int] = None


class JournalEntryCreate(JournalEntryBase):
    lines: List[JournalEntryLineCreate] = []


class JournalEntryUpdate(BaseModel):
    entry_date: Optional[datetime] = None
    description: Optional[str] = None
    lines: Optional[List[JournalEntryLineCreate]] = None


class JournalEntryResponse(JournalEntryBase):
    id: int
    entry_number: str
    status: str
    is_posted: bool
    reversed_entry_id: Optional[int] = None
    reversal_reason: Optional[str] = None
    created_by: Optional[int] = None
    posted_by: Optional[int] = None
    posted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    lines: List[JournalEntryLineResponse] = []

    class Config:
        from_attributes = True


class JournalEntrySimple(BaseModel):
    id: int
    entry_number: str
    entry_date: datetime
    description: Optional[str] = None
    status: str
    total_debit: float = 0
    total_credit: float = 0

    class Config:
        from_attributes = True
