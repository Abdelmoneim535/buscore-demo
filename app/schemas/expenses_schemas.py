from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from decimal import Decimal


# ============================================================
# Schemas لتصنيفات المصروفات
# ============================================================

class ExpenseCategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="اسم التصنيف بالعربي")
    name_en: Optional[str] = Field(None, max_length=100, description="اسم التصنيف بالإنجليزي")
    icon: Optional[str] = Field("fa-receipt", max_length=50, description="أيقونة FontAwesome")
    is_active: bool = True


class ExpenseCategoryCreate(ExpenseCategoryBase):
    pass


class ExpenseCategoryResponse(ExpenseCategoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# Schemas للمصروفات
# ============================================================

class ExpenseBase(BaseModel):
    category_id: int
    amount: Decimal = Field(..., gt=0, description="المبلغ (أكبر من صفر)")
    description: Optional[str] = None
    expense_date: datetime
    payment_method: Optional[str] = Field("cash", description="cash, bank, cheque")
    bus_id: Optional[int] = Field(None, description="ربط اختياري بحافلة معينة")


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseResponse(ExpenseBase):
    id: int
    created_at: datetime
    category: Optional[ExpenseCategoryResponse] = None

    class Config:
        from_attributes = True


# ============================================================
# Schemas للتقارير المالية
# ============================================================

class FinancialSummary(BaseModel):
    """ملخص مالي لفترة معينة"""
    period_start: datetime
    period_end: datetime
    total_revenue: Decimal = Field(..., description="إجمالي الإيرادات (من الحجوزات المؤكدة)")
    total_expenses: Decimal = Field(..., description="إجمالي المصروفات")
    net_profit: Decimal = Field(..., description="صافي الربح = الإيرادات - المصروفات")
    bookings_count: int = Field(0, description="عدد الحجوزات في الفترة")
    expenses_count: int = Field(0, description="عدد المصروفات في الفترة")


class ExpenseBreakdownItem(BaseModel):
    """بند واحد من تفصيل المصروفات حسب التصنيف"""
    category_id: int
    category_name: str
    category_name_en: Optional[str] = None
    icon: Optional[str] = None
    total_amount: Decimal
    count: int


class FinancialReport(BaseModel):
    """تقرير مالي شامل"""
    summary: FinancialSummary
    expense_breakdown: list[ExpenseBreakdownItem] = []