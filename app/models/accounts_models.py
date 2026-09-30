# -*- coding: utf-8 -*-
"""شجرة الحسابات"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base


class Account(Base):
    """حساب في شجرة الحسابات"""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=True)
    account_type = Column(String(20), nullable=False, index=True)  # asset/liability/equity/revenue/expense
    parent_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    level = Column(Integer, default=1)
    nature = Column(String(10), default="debit")  # debit / credit

    # الرصيد الافتتاحي
    opening_balance = Column(Numeric(12, 2), default=0)
    opening_balance_date = Column(DateTime(timezone=True), nullable=True)

    # الإعدادات
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    currency = Column(String(10), default="SDG")

    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # العلاقات
    parent = relationship("Account", remote_side=[id], backref="children")
    journal_lines = relationship("JournalEntryLine", back_populates="account")

    def __repr__(self):
        return f"<Account {self.code} - {self.name}>"
