# -*- coding: utf-8 -*-
"""الفترات المحاسبية"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.database.database import Base


class FiscalPeriod(Base):
    """فترة محاسبية (شهر/ربع/سنة)"""
    __tablename__ = "fiscal_periods"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)       # "سبتمبر 2026"
    name_en = Column(String(50), nullable=True)
    period_type = Column(String(20), default="monthly")  # monthly / quarterly / yearly
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(String(20), default="open")     # open / closed / locked
    closed_by = Column(Integer, nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<FiscalPeriod {self.name} [{self.status}]>"
