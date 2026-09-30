from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func, or_
from datetime import datetime
from decimal import Decimal
from typing import Optional
from app.models.employees_models import Employee, EmployeeTransaction
from app.models.expenses_models import Expense, ExpenseCategory
from app.schemas.employees_schemas import (
    EmployeeCreate,
    EmployeeTransactionCreate,
)


# ============================================================
# CRUD — العاملون
# ============================================================

def get_employee(db: Session, employee_id: int):
    return db.query(Employee).filter(Employee.id == employee_id).first()


def get_employees(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    search: Optional[str] = None,
):
    query = db.query(Employee)
    if active_only:
        query = query.filter(Employee.is_active == True)
    if search:
        term = f"%{search}%"
        query = query.filter(or_(
            Employee.full_name.ilike(term),
            Employee.full_name_en.ilike(term),
            Employee.phone.ilike(term),
            Employee.position.ilike(term),
        ))
    return query.order_by(Employee.id.desc()).offset(skip).limit(limit).all()


def create_employee(db: Session, emp: EmployeeCreate):
    db_emp = Employee(
        full_name=emp.full_name,
        full_name_en=emp.full_name_en,
        position=emp.position,
        position_en=emp.position_en,
        phone=emp.phone,
        id_number=emp.id_number,
        hire_date=emp.hire_date,
        base_salary=emp.base_salary or Decimal("0"),
        is_active=emp.is_active,
        notes=emp.notes,
    )
    db.add(db_emp)
    db.commit()
    db.refresh(db_emp)
    return db_emp


def update_employee(db: Session, employee_id: int, emp: EmployeeCreate):
    db_emp = get_employee(db, employee_id)
    if not db_emp:
        return None
    db_emp.full_name = emp.full_name
    db_emp.full_name_en = emp.full_name_en
    db_emp.position = emp.position
    db_emp.position_en = emp.position_en
    db_emp.phone = emp.phone
    db_emp.id_number = emp.id_number
    db_emp.hire_date = emp.hire_date
    db_emp.base_salary = emp.base_salary or Decimal("0")
    db_emp.is_active = emp.is_active
    db_emp.notes = emp.notes
    db.commit()
    db.refresh(db_emp)
    return db_emp


def delete_employee(db: Session, employee_id: int):
    """حذف موظف (يُحذف معه كل حركاته)"""
    db_emp = get_employee(db, employee_id)
    if not db_emp:
        return None
    db.delete(db_emp)
    db.commit()
    return db_emp


# ============================================================
# Helper: جلب/إنشاء تصنيف مصروف
# ============================================================

def _get_or_create_category(db: Session, name_ar: str, name_en: str, icon: str):
    """يبحث عن تصنيف باسمه الإنجليزي، وإن لم يجده يُنشئه"""
    cat = db.query(ExpenseCategory).filter(ExpenseCategory.name_en == name_en).first()
    if cat:
        return cat
    cat = ExpenseCategory(name=name_ar, name_en=name_en, icon=icon, is_active=True)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


# ============================================================
# CRUD — الحركات المالية
# ============================================================

def get_transaction(db: Session, transaction_id: int):
    return db.query(EmployeeTransaction).filter(EmployeeTransaction.id == transaction_id).first()


def get_transactions(
    db: Session,
    employee_id: Optional[int] = None,
    transaction_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 500,
):
    query = db.query(EmployeeTransaction)
    if employee_id:
        query = query.filter(EmployeeTransaction.employee_id == employee_id)
    if transaction_type:
        query = query.filter(EmployeeTransaction.transaction_type == transaction_type)
    if date_from:
        query = query.filter(EmployeeTransaction.transaction_date >= date_from)
    if date_to:
        query = query.filter(EmployeeTransaction.transaction_date <= date_to)
    return query.order_by(EmployeeTransaction.transaction_date.desc()).offset(skip).limit(limit).all()


def create_transaction(db: Session, txn: EmployeeTransactionCreate):
    """
    إنشاء حركة مالية + ربط تلقائي بمصروف (إن كان النوع يستدعي ذلك)
    - salary  → مصروف "رواتب"
    - advance → مصروف "سلف موظفين"
    - bonus   → مصروف "بدلات ومكافآت"
    - deduction → لا مصروف
    """
    emp = get_employee(db, txn.employee_id)
    if not emp:
        return None

    expense_id = None

    # ✅ إنشاء مصروف تلقائي
    if txn.transaction_type in ("salary", "advance", "bonus"):
        category_map = {
            "salary": ("رواتب", "Salaries", "fa-users"),
            "advance": ("سلف موظفين", "Employee Advances", "fa-hand-holding-usd"),
            "bonus": ("بدلات ومكافآت", "Bonuses", "fa-gift"),
        }
        name_ar, name_en, icon = category_map[txn.transaction_type]
        cat = _get_or_create_category(db, name_ar, name_en, icon)

        description = f"[{emp.full_name}]"
        if txn.transaction_type == "salary" and txn.period_month and txn.period_year:
            description += f" - راتب {txn.period_month}/{txn.period_year}"
        elif txn.transaction_type == "advance":
            description += " - سلفة"
        elif txn.transaction_type == "bonus":
            description += " - مكافأة"
        if txn.notes:
            description += f" - {txn.notes}"

        db_expense = Expense(
            category_id=cat.id,
            amount=txn.amount,
            description=description,
            expense_date=txn.transaction_date,
            payment_method=txn.payment_method or "cash",
            bus_id=None,
        )
        db.add(db_expense)
        db.commit()
        db.refresh(db_expense)
        expense_id = db_expense.id

    db_txn = EmployeeTransaction(
        employee_id=txn.employee_id,
        transaction_type=txn.transaction_type,
        amount=txn.amount,
        transaction_date=txn.transaction_date,
        period_month=txn.period_month,
        period_year=txn.period_year,
        payment_method=txn.payment_method,
        notes=txn.notes,
        expense_id=expense_id,
    )
    db.add(db_txn)
    db.commit()
    db.refresh(db_txn)
    return db_txn


def update_transaction(db: Session, transaction_id: int, txn: EmployeeTransactionCreate):
    """تعديل حركة — ملاحظة: لا يحدّث المصروف المرتبط تلقائيًا"""
    db_txn = get_transaction(db, transaction_id)
    if not db_txn:
        return None
    db_txn.transaction_type = txn.transaction_type
    db_txn.amount = txn.amount
    db_txn.transaction_date = txn.transaction_date
    db_txn.period_month = txn.period_month
    db_txn.period_year = txn.period_year
    db_txn.payment_method = txn.payment_method
    db_txn.notes = txn.notes
    db.commit()
    db.refresh(db_txn)
    return db_txn


def delete_transaction(db: Session, transaction_id: int):
    """حذف حركة + حذف المصروف المرتبط إن وُجد"""
    db_txn = get_transaction(db, transaction_id)
    if not db_txn:
        return None

    # حذف المصروف المرتبط
    if db_txn.expense_id:
        db_exp = db.query(Expense).filter(Expense.id == db_txn.expense_id).first()
        if db_exp:
            db.delete(db_exp)

    db.delete(db_txn)
    db.commit()
    return db_txn


# ============================================================
# كشف حساب موظف
# ============================================================

def get_employee_statement(db: Session, employee_id: int):
    emp = get_employee(db, employee_id)
    if not emp:
        return None

    transactions = db.query(EmployeeTransaction).filter(
        EmployeeTransaction.employee_id == employee_id
    ).order_by(EmployeeTransaction.transaction_date.desc()).all()

    total_salary = Decimal("0")
    total_advance = Decimal("0")
    total_deduction = Decimal("0")
    total_bonus = Decimal("0")

    for t in transactions:
        if t.transaction_type == "salary":
            total_salary += t.amount
        elif t.transaction_type == "advance":
            total_advance += t.amount
        elif t.transaction_type == "deduction":
            total_deduction += t.amount
        elif t.transaction_type == "bonus":
            total_bonus += t.amount

    # الرصيد: (السلف + المكافآت) − (الخصومات)
    balance = (total_advance + total_bonus) - total_deduction

    return {
        "summary": {
            "employee": emp,
            "total_salary": total_salary,
            "total_advance": total_advance,
            "total_deduction": total_deduction,
            "total_bonus": total_bonus,
            "balance": balance,
            "transactions_count": len(transactions),
        },
        "transactions": transactions,
    }
