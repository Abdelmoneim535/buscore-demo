# -*- coding: utf-8 -*-
"""إعدادات النظام المحاسبي"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Date
from sqlalchemy.sql import func
from app.database.database import Base


class AccountingSettings(Base):
    """إعدادات النظام المحاسبي  مرنة حسب كل شركة"""
    __tablename__ = "accounting_settings"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, default=1)

    # المستوى
    tier = Column(String(20), default="simple")  # simple / medium / full

    # الميزات
    enable_double_entry = Column(Boolean, default=False)
    enable_journal = Column(Boolean, default=False)
    enable_ledger = Column(Boolean, default=False)
    enable_trial_balance = Column(Boolean, default=False)
    enable_balance_sheet = Column(Boolean, default=False)
    enable_income_statement = Column(Boolean, default=True)
    enable_depreciation = Column(Boolean, default=False)
    enable_fiscal_periods = Column(Boolean, default=False)
    enable_audit_log = Column(Boolean, default=False)
    enable_cost_centers = Column(Boolean, default=False)
    enable_tax = Column(Boolean, default=False)
    enable_multi_currency = Column(Boolean, default=False)

    # الضرائب (افتراضي 0%)
    vat_rate = Column(Numeric(5, 2), default=0)
    income_tax_rate = Column(Numeric(5, 2), default=0)
    sales_tax_rate = Column(Numeric(5, 2), default=0)

    # طرق
    depreciation_method = Column(String(20), default="straight_line")
    inventory_method = Column(String(20), default="fifo")

    # عام
    fiscal_year_start = Column(Date, nullable=True)
    base_currency = Column(String(10), default="SDG")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<AccountingSettings tier={self.tier}>"
