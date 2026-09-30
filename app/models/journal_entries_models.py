# -*- coding: utf-8 -*-
"""دفتر اليومية  رأس القيد + التفاصيل"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base


class JournalEntry(Base):
    """رأس القيد المحاسبي"""
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    entry_number = Column(String(30), unique=True, nullable=False, index=True)
    entry_date = Column(DateTime, nullable=False, index=True)
    entry_type = Column(String(20), default="normal")  # opening/normal/closing/reversal/adjustment
    description = Column(Text, nullable=True)
    reference_type = Column(String(30), nullable=True)  # booking/payment/expense/salary/manual
    reference_id = Column(Integer, nullable=True, index=True)

    # الربط
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    fiscal_period_id = Column(Integer, ForeignKey("fiscal_periods.id"), nullable=True)

    # الحالة
    status = Column(String(20), default="draft", index=True)  # draft/posted/reversed/void
    is_posted = Column(Boolean, default=False)

    # الإلغاء
    reversed_entry_id = Column(Integer, nullable=True)
    reversal_reason = Column(Text, nullable=True)

    # التدقيق
    created_by = Column(Integer, nullable=True)
    posted_by = Column(Integer, nullable=True)
    posted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # العلاقات
    lines = relationship("JournalEntryLine", back_populates="entry", cascade="all, delete-orphan")
    fiscal_period = relationship("FiscalPeriod")

    @property
    def total_debit(self):
        return sum(float(l.debit or 0) for l in self.lines)

    @property
    def total_credit(self):
        return sum(float(l.credit or 0) for l in self.lines)

    @property
    def is_balanced(self):
        return abs(self.total_debit - self.total_credit) < 0.01

    def __repr__(self):
        return f"<JournalEntry {self.entry_number} [{self.status}]>"


class JournalEntryLine(Base):
    """تفاصيل القيد (مدين/دائن)"""
    __tablename__ = "journal_entry_lines"

    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    debit = Column(Numeric(12, 2), default=0)
    credit = Column(Numeric(12, 2), default=0)
    description = Column(Text, nullable=True)
    cost_center_id = Column(Integer, ForeignKey("cost_centers.id"), nullable=True)
    line_order = Column(Integer, default=0)

    # العلاقات
    entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("Account", back_populates="journal_lines")
    cost_center = relationship("CostCenter")

    def __repr__(self):
        return f"<JournalEntryLine account={self.account_id} D={self.debit} C={self.credit}>"
