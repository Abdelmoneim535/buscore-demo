from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base


class Employee(Base):
    """العاملون (سائقون، موظفون، إداريون)"""
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(200), nullable=False)
    full_name_en = Column(String(200), nullable=True)
    position = Column(String(100), nullable=True)
    position_en = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    id_number = Column(String(50), nullable=True)
    hire_date = Column(DateTime(timezone=True), nullable=True)
    base_salary = Column(Numeric(12, 2), nullable=True, default=0)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    #  الفرع
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)

    branch = relationship("Branch", back_populates="employees")
    transactions = relationship(
        "EmployeeTransaction",
        back_populates="employee",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Employee {self.id} - {self.full_name}>"


class EmployeeTransaction(Base):
    """كل الحركات المالية للموظف: راتب، سلفة، خصم، مكافأة"""
    __tablename__ = "employee_transactions"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)

    # نوع الحركة: salary, advance, deduction, bonus
    transaction_type = Column(String(20), nullable=False)

    amount = Column(Numeric(12, 2), nullable=False)
    transaction_date = Column(DateTime(timezone=True), nullable=False)

    # للرواتب: الشهر والسنة
    period_month = Column(Integer, nullable=True)
    period_year = Column(Integer, nullable=True)

    payment_method = Column(String(30), nullable=True, default="cash")
    notes = Column(Text, nullable=True)

    # ربط بالمصروفات (تلقائي)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    employee = relationship("Employee", back_populates="transactions")

    def __repr__(self):
        return f"<EmployeeTransaction {self.id} - {self.transaction_type} - {self.amount}>"
