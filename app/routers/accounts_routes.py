# -*- coding: utf-8 -*-
"""Router: شجرة الحسابات"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database.database import get_db
from app.routers.auth_routes import get_current_admin
from app.crud import accounts_crud
from app.schemas.accounts_schemas import (
    AccountCreate, AccountUpdate, AccountResponse,
    AccountSimple, AccountTree,
)

router = APIRouter(prefix="/accounts", tags=["شجرة الحسابات"])


# 
# قراءة (عام)
# 

@router.get("/", response_model=List[AccountResponse])
def get_accounts(
    skip: int = 0,
    limit: int = 500,
    account_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """قائمة الحسابات مع فلترة"""
    return accounts_crud.get_accounts(
        db, skip=skip, limit=limit,
        account_type=account_type, is_active=is_active, search=search,
    )


@router.get("/count")
def get_accounts_count(
    account_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """عدد الحسابات"""
    return {"count": accounts_crud.get_accounts_count(db, account_type=account_type, is_active=is_active)}


@router.get("/roots", response_model=List[AccountResponse])
def get_root_accounts(db: Session = Depends(get_db)):
    """الحسابات الرئيسية (بدون أب)"""
    return accounts_crud.get_root_accounts(db)


@router.get("/tree")
def get_account_tree(db: Session = Depends(get_db)):
    """الشجرة الكاملة"""
    return accounts_crud.get_account_tree(db)


@router.get("/summary")
def get_accounts_summary(db: Session = Depends(get_db)):
    """ملخص الحسابات"""
    return accounts_crud.get_accounts_summary(db)


@router.get("/type/{account_type}", response_model=List[AccountResponse])
def get_accounts_by_type(account_type: str, db: Session = Depends(get_db)):
    """الحسابات حسب النوع"""
    return accounts_crud.get_accounts_by_type(db, account_type)


@router.get("/code/{code}", response_model=AccountResponse)
def get_account_by_code(code: str, db: Session = Depends(get_db)):
    """بحث بالكود"""
    account = accounts_crud.get_account_by_code(db, code)
    if not account:
        raise HTTPException(status_code=404, detail="الحساب غير موجود")
    return account


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(account_id: int, db: Session = Depends(get_db)):
    """جلب حساب بالمعرف"""
    account = accounts_crud.get_account(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="الحساب غير موجود")
    return account


@router.get("/{account_id}/balance")
def get_account_balance(account_id: int, db: Session = Depends(get_db)):
    """رصيد الحساب"""
    balance = accounts_crud.get_account_balance(db, account_id)
    if not balance:
        raise HTTPException(status_code=404, detail="الحساب غير موجود")
    return balance


@router.get("/{account_id}/movements")
def get_account_movements(
    account_id: int,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    limit: int = 500,
    db: Session = Depends(get_db),
):
    """حركات الحساب"""
    return accounts_crud.get_account_movements(
        db, account_id, from_date=from_date, to_date=to_date, limit=limit,
    )


# 
# محمي
# 

@router.post("/", response_model=AccountResponse, dependencies=[Depends(get_current_admin)])
def create_account(account: AccountCreate, db: Session = Depends(get_db)):
    """إنشاء حساب جديد"""
    result = accounts_crud.create_account(db, account)
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.put("/{account_id}", response_model=AccountResponse, dependencies=[Depends(get_current_admin)])
def update_account(account_id: int, account: AccountUpdate, db: Session = Depends(get_db)):
    """تعديل حساب"""
    result = accounts_crud.update_account(db, account_id, account)
    if result is None:
        raise HTTPException(status_code=404, detail="الحساب غير موجود")
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.put("/{account_id}/toggle", response_model=AccountResponse, dependencies=[Depends(get_current_admin)])
def toggle_account(account_id: int, db: Session = Depends(get_db)):
    """تفعيل/تعطيل"""
    result = accounts_crud.toggle_account_active(db, account_id)
    if result is None:
        raise HTTPException(status_code=404, detail="الحساب غير موجود")
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.put("/{account_id}/lock", response_model=AccountResponse, dependencies=[Depends(get_current_admin)])
def lock_account(account_id: int, locked: bool = True, db: Session = Depends(get_db)):
    """قفل/فتح حساب"""
    result = accounts_crud.lock_account(db, account_id, locked)
    if result is None:
        raise HTTPException(status_code=404, detail="الحساب غير موجود")
    return result
