# -*- coding: utf-8 -*-
"""CRUD لدفتر اليومية (Journal Entries)"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from typing import Optional, List, Dict
from datetime import datetime
from decimal import Decimal
import json

from app.models.journal_entries_models import JournalEntry, JournalEntryLine
from app.models.journal_entry_audit_models import JournalEntryAudit
from app.models.accounts_models import Account
from app.schemas.journal_entries_schemas import (
    JournalEntryCreate, JournalEntryUpdate, JournalEntryLineCreate
)


# 
# توليد رقم القيد
# 

def generate_entry_number(db: Session) -> str:
    """توليد رقم قيد فريد: JE-YYYYMMDD-NNNN"""
    import datetime as dt
    date_str = dt.datetime.now().strftime('%Y%m%d')

    last = db.query(JournalEntry).filter(
        JournalEntry.entry_number.like(f'JE-{date_str}-%')
    ).order_by(desc(JournalEntry.entry_number)).first()

    if last and last.entry_number:
        try:
            last_num = int(last.entry_number.split('-')[-1])
            new_num = last_num + 1
        except (ValueError, IndexError):
            new_num = 1
    else:
        new_num = 1

    return f'JE-{date_str}-{str(new_num).zfill(4)}'


# 
# التحقق من التوازن
# 

def validate_entry_balance(lines: List) -> Dict:
    """التحقق من توازن القيد (مدين = دائن)"""
    total_debit = Decimal("0")
    total_credit = Decimal("0")

    for line in lines:
        d = line.debit if hasattr(line, "debit") else line.get("debit", 0)
        c = line.credit if hasattr(line, "credit") else line.get("credit", 0)
        total_debit += Decimal(str(d or 0))
        total_credit += Decimal(str(c or 0))

    diff = abs(total_debit - total_credit)

    return {
        "is_balanced": diff < Decimal("0.01"),
        "total_debit": float(total_debit),
        "total_credit": float(total_credit),
        "difference": float(diff),
    }


# 
# سجل التدقيق
# 

def log_audit(
    db: Session,
    entry_id: int,
    action: str,
    old_value: Optional[dict] = None,
    new_value: Optional[dict] = None,
    performed_by: Optional[int] = None,
    notes: Optional[str] = None,
):
    """تسجيل عملية في سجل التدقيق"""
    audit = JournalEntryAudit(
        entry_id=entry_id,
        action=action,
        old_value=json.dumps(old_value, ensure_ascii=False, default=str) if old_value else None,
        new_value=json.dumps(new_value, ensure_ascii=False, default=str) if new_value else None,
        performed_by=performed_by,
        notes=notes,
    )
    db.add(audit)
    db.commit()
    return audit


# 
# قراءة
# 

def get_entry(db: Session, entry_id: int) -> Optional[JournalEntry]:
    """جلب قيد بالمعرف"""
    return db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()


def get_entry_by_number(db: Session, entry_number: str) -> Optional[JournalEntry]:
    """جلب قيد برقم القيد"""
    return db.query(JournalEntry).filter(
        JournalEntry.entry_number == entry_number
    ).first()


def get_entries(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    entry_type: Optional[str] = None,
    reference_type: Optional[str] = None,
    branch_id: Optional[int] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
) -> List[JournalEntry]:
    """قائمة القيود مع فلترة"""
    query = db.query(JournalEntry)

    if status:
        query = query.filter(JournalEntry.status == status)
    if entry_type:
        query = query.filter(JournalEntry.entry_type == entry_type)
    if reference_type:
        query = query.filter(JournalEntry.reference_type == reference_type)
    if branch_id:
        query = query.filter(JournalEntry.branch_id == branch_id)
    if from_date:
        query = query.filter(JournalEntry.entry_date >= from_date)
    if to_date:
        query = query.filter(JournalEntry.entry_date <= to_date)

    return query.order_by(desc(JournalEntry.entry_date), desc(JournalEntry.id)).offset(skip).limit(limit).all()


def get_entries_count(
    db: Session,
    status: Optional[str] = None,
) -> int:
    """عدد القيود"""
    query = db.query(JournalEntry)
    if status:
        query = query.filter(JournalEntry.status == status)
    return query.count()


# 
# إنشاء
# 

def create_entry(
    db: Session,
    entry: JournalEntryCreate,
    created_by: Optional[int] = None,
    auto_commit: bool = True,
):
    """إنشاء قيد جديد (مسودة)"""
    #  التحقق من التوازن
    balance_check = validate_entry_balance(entry.lines)
    if not balance_check["is_balanced"]:
        return {
            "error": "unbalanced_entry",
            "message": f"القيد غير متوازن  الفرق: {balance_check['difference']}",
            "total_debit": balance_check["total_debit"],
            "total_credit": balance_check["total_credit"],
        }

    #  التحقق من أن القيد له سطران على الأقل
    if len(entry.lines) < 2:
        return {
            "error": "insufficient_lines",
            "message": "القيد يحتاج سطرين على الأقل (مدين + دائن)",
        }

    #  التحقق من الحسابات
    for line in entry.lines:
        account = db.query(Account).filter(Account.id == line.account_id).first()
        if not account:
            return {
                "error": "account_not_found",
                "message": f"الحساب {line.account_id} غير موجود",
            }
        if not account.is_active:
            return {
                "error": "account_inactive",
                "message": f"الحساب '{account.name}' غير نشط",
            }

    # إنشاء رقم القيد
    entry_number = generate_entry_number(db)

    # إنشاء القيد
    db_entry = JournalEntry(
        entry_number=entry_number,
        entry_date=entry.entry_date,
        entry_type=entry.entry_type or "normal",
        description=entry.description,
        reference_type=entry.reference_type,
        reference_id=entry.reference_id,
        branch_id=entry.branch_id,
        customer_id=entry.customer_id,
        booking_id=entry.booking_id,
        fiscal_period_id=entry.fiscal_period_id,
        status="draft",
        is_posted=False,
        created_by=created_by,
    )
    db.add(db_entry)
    db.flush()

    # إضافة السطور
    for i, line in enumerate(entry.lines):
        db_line = JournalEntryLine(
            entry_id=db_entry.id,
            account_id=line.account_id,
            debit=line.debit or 0,
            credit=line.credit or 0,
            description=line.description,
            cost_center_id=line.cost_center_id,
            line_order=line.line_order if line.line_order else i,
        )
        db.add(db_line)

    if auto_commit:
        db.commit()
        db.refresh(db_entry)
        # تسجيل في سجل التدقيق
        log_audit(db, db_entry.id, "create", new_value={
            "entry_number": entry_number,
            "total_debit": balance_check["total_debit"],
            "total_credit": balance_check["total_credit"],
        }, performed_by=created_by)
    else:
        db.flush()

    return db_entry


# 
# تعديل
# 

def update_entry(
    db: Session,
    entry_id: int,
    entry: JournalEntryUpdate,
    performed_by: Optional[int] = None,
):
    """تعديل قيد  المسودات فقط"""
    db_entry = get_entry(db, entry_id)
    if not db_entry:
        return None

    if db_entry.status != "draft":
        return {
            "error": "entry_not_draft",
            "message": f"لا يمكن تعديل قيد بحالة '{db_entry.status}'  المسودات فقط",
        }

    # حفظ القيمة القديمة للتدقيق
    old_value = {
        "description": db_entry.description,
        "entry_date": str(db_entry.entry_date),
    }

    # تعديل الحقول
    update_data = entry.model_dump(exclude_unset=True)

    if "description" in update_data:
        db_entry.description = update_data["description"]
    if "entry_date" in update_data:
        db_entry.entry_date = update_data["entry_date"]

    # تعديل السطور (إذا وُجدت)
    if "lines" in update_data and update_data["lines"] is not None:
        # التحقق من التوازن
        balance_check = validate_entry_balance(update_data["lines"])
        if not balance_check["is_balanced"]:
            return {
                "error": "unbalanced_entry",
                "message": f"القيد غير متوازن  الفرق: {balance_check['difference']}",
            }

        # حذف السطور القديمة
        db.query(JournalEntryLine).filter(JournalEntryLine.entry_id == entry_id).delete()

        # إضافة السطور الجديدة
        for i, line in enumerate(update_data["lines"]):
            db_line = JournalEntryLine(
                entry_id=entry_id,
                account_id=line["account_id"] if isinstance(line, dict) else line.account_id,
                debit=line["debit"] if isinstance(line, dict) else (line.debit or 0),
                credit=line["credit"] if isinstance(line, dict) else (line.credit or 0),
                description=line["description"] if isinstance(line, dict) else line.description,
                cost_center_id=line["cost_center_id"] if isinstance(line, dict) else line.cost_center_id,
                line_order=i,
            )
            db.add(db_line)

    db.commit()
    db.refresh(db_entry)

    log_audit(db, entry_id, "update", old_value=old_value, new_value={
        "description": db_entry.description,
    }, performed_by=performed_by)

    return db_entry


# 
# ترحيل / إلغاء ترحيل
# 

def post_entry(db: Session, entry_id: int, performed_by: Optional[int] = None):
    """ترحيل القيد (draft  posted)"""
    db_entry = get_entry(db, entry_id)
    if not db_entry:
        return None

    if db_entry.status != "draft":
        return {
            "error": "entry_not_draft",
            "message": f"لا يمكن ترحيل قيد بحالة '{db_entry.status}'",
        }

    # التحقق من التوازن
    if not db_entry.is_balanced:
        return {
            "error": "unbalanced_entry",
            "message": f"القيد غير متوازن  مدين: {db_entry.total_debit}, دائن: {db_entry.total_credit}",
        }

    # التحقق من السطور
    if len(db_entry.lines) < 2:
        return {
            "error": "insufficient_lines",
            "message": "القيد يحتاج سطرين على الأقل",
        }

    db_entry.status = "posted"
    db_entry.is_posted = True
    db_entry.posted_by = performed_by
    db_entry.posted_at = datetime.now()
    db.commit()
    db.refresh(db_entry)

    log_audit(db, entry_id, "post", performed_by=performed_by)

    return db_entry


def unpost_entry(db: Session, entry_id: int, performed_by: Optional[int] = None):
    """إلغاء ترحيل القيد (posted  draft)"""
    db_entry = get_entry(db, entry_id)
    if not db_entry:
        return None

    if db_entry.status != "posted":
        return {
            "error": "entry_not_posted",
            "message": f"القيد ليس بحالة 'posted'",
        }

    db_entry.status = "draft"
    db_entry.is_posted = False
    db_entry.posted_by = None
    db_entry.posted_at = None
    db.commit()
    db.refresh(db_entry)

    log_audit(db, entry_id, "unpost", performed_by=performed_by)

    return db_entry


# 
# قيد عكسي (Reversal)
# 

def reverse_entry(
    db: Session,
    entry_id: int,
    reason: str,
    performed_by: Optional[int] = None,
):
    """إنشاء قيد عكسي للقيد الأصلي"""
    original = get_entry(db, entry_id)
    if not original:
        return None

    if original.status != "posted":
        return {
            "error": "entry_not_posted",
            "message": "لا يمكن عكس قيد غير مرحَّل",
        }

    # إنشاء رقم قيد جديد
    entry_number = generate_entry_number(db)

    # إنشاء القيد العكسي (نفس القيد لكن معكوس)
    reversal = JournalEntry(
        entry_number=entry_number,
        entry_date=datetime.now(),
        entry_type="reversal",
        description=f"قيد عكسي للقيد {original.entry_number}  السبب: {reason}",
        reference_type=original.reference_type,
        reference_id=original.reference_id,
        branch_id=original.branch_id,
        customer_id=original.customer_id,
        booking_id=original.booking_id,
        status="posted",
        is_posted=True,
        reversed_entry_id=original.id,
        reversal_reason=reason,
        created_by=performed_by,
        posted_by=performed_by,
        posted_at=datetime.now(),
    )
    db.add(reversal)
    db.flush()

    # عكس السطور
    for line in original.lines:
        reverse_line = JournalEntryLine(
            entry_id=reversal.id,
            account_id=line.account_id,
            debit=line.credit or 0,    # عكس
            credit=line.debit or 0,     # عكس
            description=f"عكس: {line.description or ''}",
            cost_center_id=line.cost_center_id,
            line_order=line.line_order,
        )
        db.add(reverse_line)

    # تحديث القيد الأصلي
    original.status = "reversed"
    original.reversed_entry_id = reversal.id

    db.commit()
    db.refresh(reversal)

    log_audit(db, entry_id, "reverse", performed_by=performed_by, notes=reason)

    return reversal


# 
# حذف
# 

def delete_draft_entry(
    db: Session,
    entry_id: int,
    performed_by: Optional[int] = None,
):
    """حذف مسودة (فقط draft)"""
    db_entry = get_entry(db, entry_id)
    if not db_entry:
        return None

    if db_entry.status != "draft":
        return {
            "error": "entry_not_draft",
            "message": "يمكن حذف المسودات فقط",
        }

    # تسجيل قبل الحذف
    log_audit(db, entry_id, "delete", old_value={
        "entry_number": db_entry.entry_number,
        "description": db_entry.description,
    }, performed_by=performed_by)

    db.delete(db_entry)
    db.commit()
    return db_entry


# 
# القيد التلقائي للحجز
# 

def create_auto_entry_for_booking(
    db: Session,
    booking,
    performed_by: Optional[int] = None,
):
    """
    إنشاء قيد تلقائي عند الحجز
    من ح/ الذمم المدينة        X
      إلى ح/ إيرادات التذاكر    X
    """
    # فحص: هل يوجد قيد سابق لهذا الحجز؟
    existing = db.query(JournalEntry).filter(
        JournalEntry.reference_type == "booking",
        JournalEntry.reference_id == booking.id,
        JournalEntry.status.in_(["draft", "posted"]),
    ).first()

    if existing:
        return {
            "error": "duplicate_entry",
            "message": f"يوجد قيد سابق للحجز {booking.booking_reference}",
            "existing_entry": existing.entry_number,
        }

    # جلب الحسابات
    receivable = db.query(Account).filter(Account.code == "1103").first()
    ticket_revenue = db.query(Account).filter(Account.code == "4001").first()
    luggage_revenue = db.query(Account).filter(Account.code == "4002").first()

    if not receivable or not ticket_revenue:
        return {
            "error": "account_not_found",
            "message": "حساب الذمم المدينة أو إيرادات التذاكر غير موجود",
        }

    # حساب المبالغ
    total_price = Decimal(str(booking.total_price or 0))

    # حساب مبلغ الأمتعة (إن وُجد)
    luggage_total = Decimal("0")
    if hasattr(booking, "luggage_associations") and booking.luggage_associations:
        for assoc in booking.luggage_associations:
            if assoc.luggage:
                luggage_total += Decimal(str(assoc.luggage.price)) * assoc.quantity

    ticket_total = total_price - luggage_total

    # بناء السطور
    lines = [
        JournalEntryLineCreate(
            account_id=receivable.id,
            debit=total_price,
            credit=0,
            description=f"حجز {booking.booking_reference}",
        ),
    ]

    if ticket_total > 0:
        lines.append(JournalEntryLineCreate(
            account_id=ticket_revenue.id,
            debit=0,
            credit=ticket_total,
            description=f"إيرادات تذاكر  {booking.booking_reference}",
        ))

    if luggage_total > 0 and luggage_revenue:
        lines.append(JournalEntryLineCreate(
            account_id=luggage_revenue.id,
            debit=0,
            credit=luggage_total,
            description=f"إيرادات أمتعة  {booking.booking_reference}",
        ))

    # إنشاء القيد
    entry_create = JournalEntryCreate(
        entry_date=datetime.now(),
        entry_type="normal",
        description=f"حجز {booking.booking_reference}",
        reference_type="booking",
        reference_id=booking.id,
        branch_id=booking.branch_id,
        customer_id=booking.customer_id,
        booking_id=booking.id,
        lines=lines,
    )

    return create_entry(db, entry_create, created_by=performed_by)
