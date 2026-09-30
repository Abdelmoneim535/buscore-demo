from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from app.models.expenses_models import Expense, ExpenseCategory
from app.models.bookings_models import Booking, BookingStatus
from app.schemas.expenses_schemas import (
    ExpenseCategoryCreate,
    ExpenseCreate,
)


# ============================================================
# CRUD — تصنيفات المصروفات
# ============================================================

def get_category(db: Session, category_id: int):
    return db.query(ExpenseCategory).filter(ExpenseCategory.id == category_id).first()


def get_categories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(ExpenseCategory).order_by(ExpenseCategory.id).offset(skip).limit(limit).all()


def create_category(db: Session, category: ExpenseCategoryCreate):
    #  التحقق من الاسم
    existing = db.query(ExpenseCategory).filter(ExpenseCategory.name == category.name).first()
    if existing:
        return {"error": "name_duplicate", "message": f"التصنيف '{category.name}' موجود مسبقًا"}

    db_cat = ExpenseCategory(
        name=category.name,
        name_en=category.name_en,
        icon=category.icon,
        is_active=category.is_active,
    )
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat


def update_category(db: Session, category_id: int, category: ExpenseCategoryCreate):
    db_cat = get_category(db, category_id)
    if not db_cat:
        return None
    db_cat.name = category.name
    db_cat.name_en = category.name_en
    db_cat.icon = category.icon
    db_cat.is_active = category.is_active
    db.commit()
    db.refresh(db_cat)
    return db_cat


def delete_category(db: Session, category_id: int):
    """لا يمكن الحذف إذا كان مرتبطًا بمصروفات"""
    db_cat = get_category(db, category_id)
    if not db_cat:
        return None

    # التحقق من وجود مصروفات مرتبطة
    count = db.query(Expense).filter(Expense.category_id == category_id).count()
    if count > 0:
        return {"error": f"لا يمكن الحذف — التصنيف مرتبط بـ {count} مصروف"}

    db.delete(db_cat)
    db.commit()
    return db_cat


# ============================================================
# CRUD — المصروفات
# ============================================================

def get_expense(db: Session, expense_id: int):
    return db.query(Expense).filter(Expense.id == expense_id).first()


def get_expenses(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    bus_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
):
    query = db.query(Expense)

    if category_id:
        query = query.filter(Expense.category_id == category_id)
    if bus_id:
        query = query.filter(Expense.bus_id == bus_id)
    if date_from:
        query = query.filter(Expense.expense_date >= date_from)
    if date_to:
        query = query.filter(Expense.expense_date <= date_to)

    return query.order_by(Expense.expense_date.desc()).offset(skip).limit(limit).all()


def create_expense(db: Session, expense: ExpenseCreate):
    db_exp = Expense(
        category_id=expense.category_id,
        amount=expense.amount,
        description=expense.description,
        expense_date=expense.expense_date,
        payment_method=expense.payment_method,
        bus_id=expense.bus_id,
    )
    db.add(db_exp)
    db.commit()
    db.refresh(db_exp)
    return db_exp


def update_expense(db: Session, expense_id: int, expense: ExpenseCreate):
    db_exp = get_expense(db, expense_id)
    if not db_exp:
        return None
    db_exp.category_id = expense.category_id
    db_exp.amount = expense.amount
    db_exp.description = expense.description
    db_exp.expense_date = expense.expense_date
    db_exp.payment_method = expense.payment_method
    db_exp.bus_id = expense.bus_id
    db.commit()
    db.refresh(db_exp)
    return db_exp


def delete_expense(db: Session, expense_id: int):
    db_exp = get_expense(db, expense_id)
    if db_exp:
        db.delete(db_exp)
        db.commit()
    return db_exp


# ============================================================
# التقارير المالية
# ============================================================

def _sum_revenue(db: Session, date_from: datetime, date_to: datetime):
    """مجموع الإيرادات من الحجوزات المؤكدة (غير ملغاة) في الفترة"""
    result = db.query(sql_func.coalesce(sql_func.sum(Booking.total_price), 0)).filter(
        Booking.booked_at >= date_from,
        Booking.booked_at <= date_to,
        Booking.status != BookingStatus.CANCELLED,
    ).scalar()
    return Decimal(result or 0)


def _sum_expenses(db: Session, date_from: datetime, date_to: datetime):
    """مجموع المصروفات في الفترة"""
    result = db.query(sql_func.coalesce(sql_func.sum(Expense.amount), 0)).filter(
        Expense.expense_date >= date_from,
        Expense.expense_date <= date_to,
    ).scalar()
    return Decimal(result or 0)


def _count_bookings(db: Session, date_from: datetime, date_to: datetime) -> int:
    return db.query(Booking).filter(
        Booking.booked_at >= date_from,
        Booking.booked_at <= date_to,
        Booking.status != BookingStatus.CANCELLED,
    ).count()


def _count_expenses(db: Session, date_from: datetime, date_to: datetime) -> int:
    return db.query(Expense).filter(
        Expense.expense_date >= date_from,
        Expense.expense_date <= date_to,
    ).count()


def get_financial_summary(db: Session, date_from: datetime, date_to: datetime):
    """ملخص مالي للفترة المحددة"""
    total_revenue = _sum_revenue(db, date_from, date_to)
    total_expenses = _sum_expenses(db, date_from, date_to)
    net_profit = total_revenue - total_expenses

    return {
        "period_start": date_from,
        "period_end": date_to,
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "bookings_count": _count_bookings(db, date_from, date_to),
        "expenses_count": _count_expenses(db, date_from, date_to),
    }


def get_expense_breakdown(db: Session, date_from: datetime, date_to: datetime):
    """تفصيل المصروفات حسب التصنيف"""
    rows = (
        db.query(
            ExpenseCategory.id,
            ExpenseCategory.name,
            ExpenseCategory.name_en,
            ExpenseCategory.icon,
            sql_func.coalesce(sql_func.sum(Expense.amount), 0).label("total_amount"),
            sql_func.count(Expense.id).label("count"),
        )
        .join(Expense, Expense.category_id == ExpenseCategory.id)
        .filter(
            Expense.expense_date >= date_from,
            Expense.expense_date <= date_to,
        )
        .group_by(ExpenseCategory.id)
        .all()
    )

    return [
        {
            "category_id": row.id,
            "category_name": row.name,
            "category_name_en": row.name_en,
            "icon": row.icon,
            "total_amount": Decimal(row.total_amount or 0),
            "count": row.count,
        }
        for row in rows
    ]


def get_full_financial_report(db: Session, date_from: datetime, date_to: datetime):
    """تقرير مالي كامل (ملخص + تفصيل)"""
    return {
        "summary": get_financial_summary(db, date_from, date_to),
        "expense_breakdown": get_expense_breakdown(db, date_from, date_to),
    }