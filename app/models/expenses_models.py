from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base


class ExpenseCategory(Base):
    """تصنيفات المصروفات (وقود، رواتب، صيانة، ...)"""
    __tablename__ = "expense_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=True)
    icon = Column(String(50), nullable=True, default="fa-receipt")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    expenses = relationship("Expense", back_populates="category")

    def __repr__(self):
        return f"<ExpenseCategory {self.name}>"


class Expense(Base):
    """المصروفات المالية"""
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("expense_categories.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    description = Column(Text, nullable=True)
    expense_date = Column(DateTime(timezone=True), nullable=False)
    payment_method = Column(String(30), nullable=True, default="cash")  # cash, bank, cheque

    # ✅ حقل اختياري لربط المصروف بحافلة معينة (للصيانة، الوقود...)
    # يسمح بتقارير تكلفة كل باص في المستقبل
    bus_id = Column(Integer, ForeignKey("buses.id"), nullable=True)
    #  الفرع
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    category = relationship("ExpenseCategory", back_populates="expenses")
    branch = relationship("Branch", back_populates="expenses")

    def __repr__(self):
        return f"<Expense {self.id} - {self.amount}>"