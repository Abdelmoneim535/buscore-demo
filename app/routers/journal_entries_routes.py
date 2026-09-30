# -*- coding: utf-8 -*-
"""Router: دفتر اليومية"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database.database import get_db
from app.routers.auth_routes import get_current_admin
from app.crud import journal_entries_crud
from app.schemas.journal_entries_schemas import (
    JournalEntryCreate, JournalEntryUpdate, JournalEntryResponse, JournalEntrySimple,
)

router = APIRouter(prefix="/journal-entries", tags=["دفتر اليومية"])


# 
# قراءة (محمي)
# 

@router.get("/", response_model=List[JournalEntryResponse], dependencies=[Depends(get_current_admin)])
def get_entries(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    entry_type: Optional[str] = None,
    reference_type: Optional[str] = None,
    branch_id: Optional[int] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    """قائمة القيود"""
    return journal_entries_crud.get_entries(
        db, skip=skip, limit=limit,
        status=status, entry_type=entry_type,
        reference_type=reference_type, branch_id=branch_id,
        from_date=from_date, to_date=to_date,
    )


@router.get("/count", dependencies=[Depends(get_current_admin)])
def get_entries_count(status: Optional[str] = None, db: Session = Depends(get_db)):
    """عدد القيود"""
    return {"count": journal_entries_crud.get_entries_count(db, status=status)}


@router.get("/{entry_id}", response_model=JournalEntryResponse, dependencies=[Depends(get_current_admin)])
def get_entry(entry_id: int, db: Session = Depends(get_db)):
    """جلب قيد"""
    entry = journal_entries_crud.get_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="القيد غير موجود")
    return entry


# 
# إنشاء / تعديل
# 

@router.post("/", response_model=JournalEntryResponse, dependencies=[Depends(get_current_admin)])
def create_entry(entry: JournalEntryCreate, db: Session = Depends(get_db)):
    """إنشاء قيد جديد (مسودة)"""
    result = journal_entries_crud.create_entry(db, entry)
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.put("/{entry_id}", response_model=JournalEntryResponse, dependencies=[Depends(get_current_admin)])
def update_entry(entry_id: int, entry: JournalEntryUpdate, db: Session = Depends(get_db)):
    """تعديل قيد (مسودة فقط)"""
    result = journal_entries_crud.update_entry(db, entry_id, entry)
    if result is None:
        raise HTTPException(status_code=404, detail="القيد غير موجود")
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
    return result


# 
# ترحيل / إلغاء / عكس
# 

@router.post("/{entry_id}/post", response_model=JournalEntryResponse, dependencies=[Depends(get_current_admin)])
def post_entry(entry_id: int, db: Session = Depends(get_db)):
    """ترحيل القيد"""
    result = journal_entries_crud.post_entry(db, entry_id)
    if result is None:
        raise HTTPException(status_code=404, detail="القيد غير موجود")
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/{entry_id}/unpost", response_model=JournalEntryResponse, dependencies=[Depends(get_current_admin)])
def unpost_entry(entry_id: int, db: Session = Depends(get_db)):
    """إلغاء الترحيل"""
    result = journal_entries_crud.unpost_entry(db, entry_id)
    if result is None:
        raise HTTPException(status_code=404, detail="القيد غير موجود")
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/{entry_id}/reverse", response_model=JournalEntryResponse, dependencies=[Depends(get_current_admin)])
def reverse_entry(entry_id: int, reason: str, db: Session = Depends(get_db)):
    """قيد عكسي"""
    result = journal_entries_crud.reverse_entry(db, entry_id, reason)
    if result is None:
        raise HTTPException(status_code=404, detail="القيد غير موجود")
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.delete("/{entry_id}", dependencies=[Depends(get_current_admin)])
def delete_draft_entry(entry_id: int, db: Session = Depends(get_db)):
    """حذف مسودة"""
    result = journal_entries_crud.delete_draft_entry(db, entry_id)
    if result is None:
        raise HTTPException(status_code=404, detail="القيد غير موجود")
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
    return {"message": f"تم حذف القيد {result.entry_number}"}
