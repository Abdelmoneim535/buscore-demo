# -*- coding: utf-8 -*-
"""Schemas: شجرة الحسابات"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal


class AccountBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=200)
    name_en: Optional[str] = None
    account_type: str  # asset/liability/equity/revenue/expense
    parent_id: Optional[int] = None
    level: int = 1
    nature: str = "debit"  # debit / credit
    opening_balance: Decimal = Decimal("0")
    opening_balance_date: Optional[datetime] = None
    is_active: bool = True
    currency: str = "SDG"
    description: Optional[str] = None


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    name_en: Optional[str] = None
    opening_balance: Optional[Decimal] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


class AccountResponse(AccountBase):
    id: int
    is_system: bool = False
    is_locked: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class AccountSimple(BaseModel):
    id: int
    code: str
    name: str
    name_en: Optional[str] = None
    account_type: str
    nature: str

    class Config:
        from_attributes = True


class AccountTree(AccountResponse):
    children: List["AccountTree"] = []

    class Config:
        from_attributes = True


AccountTree.model_rebuild()
