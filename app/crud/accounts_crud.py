# -*- coding: utf-8 -*-
"""CRUD لشجرة الحسابات"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from typing import Optional, List, Dict
from datetime import datetime
from decimal import Decimal

from app.models.accounts_models import Account
from app.schemas.accounts_schemas import AccountCreate, AccountUpdate


# 
# قراءة
# 

def get_account(db: Session, account_id: int) -> Optional[Account]:
    """جلب حساب بالمعرف"""
    return db.query(Account).filter(Account.id == account_id).first()


def get_account_by_code(db: Session, code: str) -> Optional[Account]:
    """جلب حساب بالكود (1000, 4001, إلخ)"""
    return db.query(Account).filter(Account.code == code).first()


def get_accounts(
    db: Session,
    skip: int = 0,
    limit: int = 500,
    account_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
) -> List[Account]:
    """قائمة الحسابات مع فلترة"""
    query = db.query(Account)

    if account_type:
        query = query.filter(Account.account_type == account_type)

    if is_active is not None:
        query = query.filter(Account.is_active == is_active)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Account.code.ilike(pattern),
                Account.name.ilike(pattern),
                Account.name_en.ilike(pattern),
            )
        )

    return query.order_by(Account.code).offset(skip).limit(limit).all()


def get_accounts_by_type(db: Session, account_type: str) -> List[Account]:
    """جلب الحسابات حسب النوع (asset/liability/equity/revenue/expense)"""
    return db.query(Account).filter(
        Account.account_type == account_type,
        Account.is_active == True,
    ).order_by(Account.code).all()


def get_root_accounts(db: Session) -> List[Account]:
    """الحسابات الرئيسية (بدون أب)"""
    return db.query(Account).filter(
        Account.parent_id.is_(None),
        Account.is_active == True,
    ).order_by(Account.code).all()


def get_account_children(db: Session, parent_id: int) -> List[Account]:
    """الحسابات الفرعية المباشرة"""
    return db.query(Account).filter(
        Account.parent_id == parent_id,
        Account.is_active == True,
    ).order_by(Account.code).all()


def get_account_tree(db: Session) -> List[Dict]:
    """شجرة الحسابات الكاملة (recursive)"""
    all_accounts = db.query(Account).filter(
        Account.is_active == True,
    ).order_by(Account.code).all()

    # بناء dictionary: id  node
    nodes = {}
    for acc in all_accounts:
        nodes[acc.id] = {
            "id": acc.id,
            "code": acc.code,
            "name": acc.name,
            "name_en": acc.name_en,
            "account_type": acc.account_type,
            "nature": acc.nature,
            "level": acc.level,
            "parent_id": acc.parent_id,
            "is_system": acc.is_system,
            "children": [],
        }

    # ربط الأبناء بالآباء
    roots = []
    for acc in all_accounts:
        node = nodes[acc.id]
        if acc.parent_id and acc.parent_id in nodes:
            nodes[acc.parent_id]["children"].append(node)
        else:
            roots.append(node)

    return roots


def get_accounts_count(
    db: Session,
    account_type: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> int:
    """عدد الحسابات"""
    query = db.query(Account)

    if account_type:
        query = query.filter(Account.account_type == account_type)

    if is_active is not None:
        query = query.filter(Account.is_active == is_active)

    return query.count()


# 
# إنشاء
# 

def create_account(db: Session, account: AccountCreate):
    """إنشاء حساب جديد"""
    # التحقق من الكود
    existing = db.query(Account).filter(Account.code == account.code).first()
    if existing:
        return {
            "error": "code_duplicate",
            "message": f"كود الحساب '{account.code}' مستخدم مسبقًا",
        }

    # التحقق من الأب
    parent_id = account.parent_id
    level = account.level

    if parent_id:
        parent = db.query(Account).filter(Account.id == parent_id).first()
        if not parent:
            return {
                "error": "parent_not_found",
                "message": "الحساب الأب غير موجود",
            }
        level = parent.level + 1

    # إنشاء الحساب
    db_account = Account(
        code=account.code,
        name=account.name,
        name_en=account.name_en,
        account_type=account.account_type,
        parent_id=parent_id,
        level=level,
        nature=account.nature,
        opening_balance=account.opening_balance or 0,
        opening_balance_date=account.opening_balance_date,
        is_active=account.is_active if account.is_active is not None else True,
        currency=account.currency or "SDG",
        description=account.description,
        is_system=False,
    )

    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


# 
# تعديل
# 

def update_account(db: Session, account_id: int, account: AccountUpdate):
    """تعديل حساب"""
    db_account = get_account(db, account_id)
    if not db_account:
        return None

    if db_account.is_locked:
        return {
            "error": "account_locked",
            "message": "الحساب مقفل  لا يمكن تعديله",
        }

    update_data = account.model_dump(exclude_unset=True)

    # منع تعديل بعض الحقول
    forbidden = ["code", "account_type", "parent_id", "nature", "is_system"]
    for field in forbidden:
        update_data.pop(field, None)

    for key, value in update_data.items():
        setattr(db_account, key, value)

    db.commit()
    db.refresh(db_account)
    return db_account


def toggle_account_active(db: Session, account_id: int):
    """تفعيل/تعطيل حساب"""
    db_account = get_account(db, account_id)
    if not db_account:
        return None

    if db_account.is_system and db_account.is_active:
        return {
            "error": "cannot_deactivate_system",
            "message": "لا يمكن تعطيل حساب نظامي",
        }

    db_account.is_active = not db_account.is_active
    db.commit()
    db.refresh(db_account)
    return db_account


def lock_account(db: Session, account_id: int, locked: bool = True):
    """قفل/فتح حساب"""
    db_account = get_account(db, account_id)
    if not db_account:
        return None

    db_account.is_locked = locked
    db.commit()
    db.refresh(db_account)
    return db_account


# 
# الأرصدة والحركات
# 

def get_account_balance(db: Session, account_id: int) -> Dict:
    """
    حساب رصيد الحساب
    - الرصيد = opening_balance + مجموع المدين - مجموع الدائن (للأصول/المصروفات)
    - أو opening_balance + مجموع الدائن - مجموع المدين (للخصوم/الإيرادات)
    """
    from app.models.journal_entries_models import JournalEntry, JournalEntryLine

    account = get_account(db, account_id)
    if not account:
        return {}

    # مجموع المدين والدائن (من القيود المرحّلة فقط)
    result = db.query(
        func.coalesce(func.sum(JournalEntryLine.debit), 0).label("total_debit"),
        func.coalesce(func.sum(JournalEntryLine.credit), 0).label("total_credit"),
    ).join(
        JournalEntry, JournalEntry.id == JournalEntryLine.entry_id
    ).filter(
        JournalEntryLine.account_id == account_id,
        JournalEntry.status == "posted",
    ).first()

    total_debit = float(result.total_debit or 0)
    total_credit = float(result.total_credit or 0)

    # الرصيد حسب طبيعة الحساب
    if account.nature == "debit":
        balance = float(account.opening_balance or 0) + total_debit - total_credit
    else:
        balance = float(account.opening_balance or 0) + total_credit - total_debit

    return {
        "account_id": account.id,
        "code": account.code,
        "name": account.name,
        "nature": account.nature,
        "opening_balance": float(account.opening_balance or 0),
        "total_debit": total_debit,
        "total_credit": total_credit,
        "balance": balance,
    }


def get_account_movements(
    db: Session,
    account_id: int,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    limit: int = 500,
) -> List[Dict]:
    """حركات الحساب (من القيود)"""
    from app.models.journal_entries_models import JournalEntry, JournalEntryLine

    query = db.query(JournalEntryLine, JournalEntry).join(
        JournalEntry, JournalEntry.id == JournalEntryLine.entry_id
    ).filter(
        JournalEntryLine.account_id == account_id,
    )

    if from_date:
        query = query.filter(JournalEntry.entry_date >= from_date)

    if to_date:
        query = query.filter(JournalEntry.entry_date <= to_date)

    query = query.order_by(asc(JournalEntry.entry_date), asc(JournalEntryLine.id))
    query = query.limit(limit)

    movements = []
    for line, entry in query.all():
        movements.append({
            "line_id": line.id,
            "entry_id": entry.id,
            "entry_number": entry.entry_number,
            "entry_date": entry.entry_date,
            "description": line.description or entry.description,
            "debit": float(line.debit or 0),
            "credit": float(line.credit or 0),
            "cost_center_id": line.cost_center_id,
            "reference_type": entry.reference_type,
            "reference_id": entry.reference_id,
        })

    return movements


# 
# إحصائيات
# 

def get_accounts_summary(db: Session) -> Dict:
    """إحصائيات عامة عن شجرة الحسابات"""
    total = db.query(Account).count()

    # حسب النوع
    types = {}
    for acc_type in ["asset", "liability", "equity", "revenue", "expense"]:
        count = db.query(Account).filter(
            Account.account_type == acc_type,
            Account.is_active == True,
        ).count()
        types[acc_type] = count

    # النشطة
    active = db.query(Account).filter(Account.is_active == True).count()
    inactive = total - active

    # النظامية
    system = db.query(Account).filter(Account.is_system == True).count()
    custom = total - system

    return {
        "total": total,
        "active": active,
        "inactive": inactive,
        "system": system,
        "custom": custom,
        "by_type": types,
    }
