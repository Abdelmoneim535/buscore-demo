from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal


# ============================================================
# Employee Schemas
# ============================================================

class EmployeeBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    full_name_en: Optional[str] = Field(None, max_length=200)
    position: Optional[str] = Field(None, max_length=100)
    position_en: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    id_number: Optional[str] = Field(None, max_length=50)
    hire_date: Optional[datetime] = None
    base_salary: Optional[Decimal] = Field(Decimal("0"), ge=0)
    is_active: bool = True
    notes: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeResponse(EmployeeBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# Employee Transaction Schemas
# ============================================================

class EmployeeTransactionBase(BaseModel):
    employee_id: int
    transaction_type: str = Field(..., description="salary, advance, deduction, bonus")
    amount: Decimal = Field(..., gt=0)
    transaction_date: datetime
    period_month: Optional[int] = Field(None, ge=1, le=12)
    period_year: Optional[int] = Field(None, ge=2000, le=2100)
    payment_method: Optional[str] = "cash"
    notes: Optional[str] = None


class EmployeeTransactionCreate(EmployeeTransactionBase):
    pass


class EmployeeTransactionResponse(EmployeeTransactionBase):
    id: int
    expense_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# Statement Schemas
# ============================================================

class EmployeeStatementSummary(BaseModel):
    employee: EmployeeResponse
    total_salary: Decimal = Field(..., description="مجموع الرواتب المدفوعة")
    total_advance: Decimal = Field(..., description="مجموع السلف")
    total_deduction: Decimal = Field(..., description="مجموع الخصومات")
    total_bonus: Decimal = Field(..., description="مجموع المكافآت")
    balance: Decimal = Field(..., description="الرصيد (سلف - خصومات متبقية)")
    transactions_count: int


class EmployeeStatement(BaseModel):
    summary: EmployeeStatementSummary
    transactions: List[EmployeeTransactionResponse] = []
