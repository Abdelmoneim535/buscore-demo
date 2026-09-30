# -*- coding: utf-8 -*-
"""CRUD للفترات المحاسبية"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from typing import Optional, List, Dict
from datetime import datetime
from decimal import Decimal

from app.models.fiscal_periods_models import FiscalPeriod
from app.schemas.fiscal_periods_schemas import FiscalPeriodCreate, FiscalPeriodUpdate


# 
# قراءة
# 

def get_period(db: Session, period_id: int) -> Optional[FiscalPeriod]:
    """جلب فترة بالمعرف"""
    return db.query(FiscalPeriod).filter(FiscalPeriod.id == period_id).first()


def get_periods(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    period_type: Optional[str] = None,
) -> List[FiscalPeriod]:
    """قائمة الفترات مع فلترة"""
    query = db.query(FiscalPeriod)

    if status:
        query = query.filter(FiscalPeriod.status == status)
    if period_type:
        query = query.filter(FiscalPeriod.period_type == period_type)

    return query.order_by(desc(FiscalPeriod.start_date)).offset(skip).limit(limit).all()


def get_periods_count(db: Session, status: Optional[str] = None) -> int:
    """عدد الفترات"""
    query = db.query(FiscalPeriod)
    if status:
        query = query.filter(FiscalPeriod.status == status)
    return query.count()


def get_current_period(db: Session) -> Optional[FiscalPeriod]:
    """الفترة الحالية (التي يشمل تاريخها الآن)"""
    now = datetime.now()
    return db.query(FiscalPeriod).filter(
        FiscalPeriod.start_date <= now,
        FiscalPeriod.end_date >= now,
        FiscalPeriod.status == "open",
    ).first()


def get_period_for_date(db: Session, date: datetime) -> Optional[FiscalPeriod]:
    """الفترة التي يشملها تاريخ معين"""
    return db.query(FiscalPeriod).filter(
        FiscalPeriod.start_date <= date,
        FiscalPeriod.end_date >= date,
    ).first()


def get_open_periods(db: Session) -> List[FiscalPeriod]:
    """الفترات المفتوحة"""
    return db.query(FiscalPeriod).filter(
        FiscalPeriod.status == "open",
    ).order_by(FiscalPeriod.start_date).all()


# 
# إنشاء
# 

def create_period(db: Session, period: FiscalPeriodCreate):
    """إنشاء فترة محاسبية جديدة"""
    # التحقق من التواريخ
    if period.end_date <= period.start_date:
        return {
            "error": "invalid_dates",
            "message": "تاريخ النهاية يجب أن يكون بعد تاريخ البداية",
        }

    # التحقق من عدم التداخل مع فترة أخرى
    overlapping = db.query(FiscalPeriod).filter(
        or_(
            and_(
                FiscalPeriod.start_date <= period.start_date,
                FiscalPeriod.end_date >= period.start_date,
            ),
            and_(
                FiscalPeriod.start_date <= period.end_date,
                FiscalPeriod.end_date >= period.end_date,
            ),
            and_(
                FiscalPeriod.start_date >= period.start_date,
                FiscalPeriod.end_date <= period.end_date,
            ),
        ),
    ).first()

    if overlapping:
        return {
            "error": "period_overlap",
            "message": f"الفترة تتداخل مع فترة أخرى: {overlapping.name}",
        }

    db_period = FiscalPeriod(
        name=period.name,
        name_en=period.name_en,
        period_type=period.period_type or "monthly",
        start_date=period.start_date,
        end_date=period.end_date,
        status=period.status or "open",
        notes=period.notes,
    )

    db.add(db_period)
    db.commit()
    db.refresh(db_period)
    return db_period


def auto_create_monthly_periods(db: Session, year: int):
    """إنشاء 12 فترة شهرية تلقائيًا لسنة"""
    from datetime import date
    import calendar

    created = []
    month_names_ar = [
        "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
        "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
    ]
    month_names_en = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    for month in range(1, 13):
        start = datetime(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end = datetime(year, month, last_day, 23, 59, 59)

        # التحقق من عدم الوجود
        existing = db.query(FiscalPeriod).filter(
            FiscalPeriod.start_date == start,
            FiscalPeriod.end_date == end,
        ).first()

        if not existing:
            period = FiscalPeriod(
                name=f"{month_names_ar[month-1]} {year}",
                name_en=f"{month_names_en[month-1]} {year}",
                period_type="monthly",
                start_date=start,
                end_date=end,
                status="open",
            )
            db.add(period)
            created.append(period)

    if created:
        db.commit()
        for p in created:
            db.refresh(p)

    return created


# 
# تعديل
# 

def update_period(db: Session, period_id: int, period: FiscalPeriodUpdate):
    """تعديل فترة"""
    db_period = get_period(db, period_id)
    if not db_period:
        return None

    if db_period.status in ("closed", "locked"):
        return {
            "error": "period_closed",
            "message": f"لا يمكن تعديل فترة {db_period.status}",
        }

    update_data = period.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_period, key, value)

    db.commit()
    db.refresh(db_period)
    return db_period


# 
# إقفال / إعادة فتح
# 

def close_period(db: Session, period_id: int, closed_by: Optional[int] = None):
    """إقفال فترة محاسبية"""
    db_period = get_period(db, period_id)
    if not db_period:
        return None

    if db_period.status == "closed":
        return {
            "error": "already_closed",
            "message": "الفترة مُقفلة مسبقًا",
        }

    if db_period.status == "locked":
        return {
            "error": "period_locked",
            "message": "الفترة مقفلة نهائيًا",
        }

    # التحقق من عدم وجود قيود مسودة في الفترة
    from app.models.journal_entries_models import JournalEntry
    draft_entries = db.query(JournalEntry).filter(
        JournalEntry.entry_date >= db_period.start_date,
        JournalEntry.entry_date <= db_period.end_date,
        JournalEntry.status == "draft",
    ).count()

    if draft_entries > 0:
        return {
            "error": "has_draft_entries",
            "message": f"يوجد {draft_entries} قيد مسودة في الفترة  يجب ترحيلها أو حذفها قبل الإقفال",
        }

    db_period.status = "closed"
    db_period.closed_by = closed_by
    db_period.closed_at = datetime.now()

    db.commit()
    db.refresh(db_period)
    return db_period


def reopen_period(db: Session, period_id: int):
    """إعادة فتح فترة مُقفلة"""
    db_period = get_period(db, period_id)
    if not db_period:
        return None

    if db_period.status == "locked":
        return {
            "error": "period_locked",
            "message": "الفترة مقفلة نهائيًا  لا يمكن إعادة فتحها",
        }

    if db_period.status == "open":
        return {
            "error": "already_open",
            "message": "الفترة مفتوحة مسبقًا",
        }

    db_period.status = "open"
    db_period.closed_by = None
    db_period.closed_at = None

    db.commit()
    db.refresh(db_period)
    return db_period


def lock_period(db: Session, period_id: int):
    """قفل نهائي للفترة"""
    db_period = get_period(db, period_id)
    if not db_period:
        return None

    db_period.status = "locked"
    db.commit()
    db.refresh(db_period)
    return db_period


# 
# ملخص الفترة
# 

def get_period_summary(db: Session, period_id: int) -> Dict:
    """ملخص الفترة (عدد القيود، الإجماليات، إلخ)"""
    from app.models.journal_entries_models import JournalEntry, JournalEntryLine

    db_period = get_period(db, period_id)
    if not db_period:
        return {}

    # القيود في الفترة
    entries = db.query(JournalEntry).filter(
        JournalEntry.entry_date >= db_period.start_date,
        JournalEntry.entry_date <= db_period.end_date,
    ).all()

    total_entries = len(entries)
    posted_entries = sum(1 for e in entries if e.status == "posted")
    draft_entries = sum(1 for e in entries if e.status == "draft")
    reversed_entries = sum(1 for e in entries if e.status == "reversed")

    # إجماليات المدين والدائن
    result = db.query(
        func.coalesce(func.sum(JournalEntryLine.debit), 0).label("total_debit"),
        func.coalesce(func.sum(JournalEntryLine.credit), 0).label("total_credit"),
    ).join(
        JournalEntry, JournalEntry.id == JournalEntryLine.entry_id
    ).filter(
        JournalEntry.entry_date >= db_period.start_date,
        JournalEntry.entry_date <= db_period.end_date,
        JournalEntry.status == "posted",
    ).first()

    return {
        "period_id": db_period.id,
        "name": db_period.name,
        "start_date": db_period.start_date,
        "end_date": db_period.end_date,
        "status": db_period.status,
        "total_entries": total_entries,
        "posted_entries": posted_entries,
        "draft_entries": draft_entries,
        "reversed_entries": reversed_entries,
        "total_debit": float(result.total_debit or 0),
        "total_credit": float(result.total_credit or 0),
        "is_balanced": abs(float(result.total_debit or 0) - float(result.total_credit or 0)) < 0.01,
    }


def is_date_in_open_period(db: Session, date: datetime) -> bool:
    """التحقق من أن التاريخ داخل فترة مفتوحة"""
    period = db.query(FiscalPeriod).filter(
        FiscalPeriod.start_date <= date,
        FiscalPeriod.end_date >= date,
        FiscalPeriod.status == "open",
    ).first()

    return period is not None
