# -*- coding: utf-8 -*-
"""Schemas: إعدادات النظام المحاسبي"""
from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional
from decimal import Decimal


class AccountingSettingsBase(BaseModel):
    tier: str = "simple"
    enable_double_entry: bool = False
    enable_journal: bool = False
    enable_ledger: bool = False
    enable_trial_balance: bool = False
    enable_balance_sheet: bool = False
    enable_income_statement: bool = True
    enable_depreciation: bool = False
    enable_fiscal_periods: bool = False
    enable_audit_log: bool = False
    enable_cost_centers: bool = False
    enable_tax: bool = False
    enable_multi_currency: bool = False
    vat_rate: Decimal = Decimal("0")
    income_tax_rate: Decimal = Decimal("0")
    sales_tax_rate: Decimal = Decimal("0")
    depreciation_method: str = "straight_line"
    inventory_method: str = "fifo"
    fiscal_year_start: Optional[date] = None
    base_currency: str = "SDG"


class AccountingSettingsUpdate(BaseModel):
    tier: Optional[str] = None
    enable_double_entry: Optional[bool] = None
    enable_journal: Optional[bool] = None
    enable_ledger: Optional[bool] = None
    enable_trial_balance: Optional[bool] = None
    enable_balance_sheet: Optional[bool] = None
    enable_income_statement: Optional[bool] = None
    enable_depreciation: Optional[bool] = None
    enable_fiscal_periods: Optional[bool] = None
    enable_audit_log: Optional[bool] = None
    enable_cost_centers: Optional[bool] = None
    enable_tax: Optional[bool] = None
    enable_multi_currency: Optional[bool] = None
    vat_rate: Optional[Decimal] = None
    income_tax_rate: Optional[Decimal] = None
    sales_tax_rate: Optional[Decimal] = None
    depreciation_method: Optional[str] = None
    inventory_method: Optional[str] = None
    fiscal_year_start: Optional[date] = None
    base_currency: Optional[str] = None


class AccountingSettingsResponse(AccountingSettingsBase):
    id: int
    company_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
