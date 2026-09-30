# -*- coding: utf-8 -*-
"""Router: الفترات المحاسبية"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.database import get_db
from app.routers.auth_routes import get_current_admin
from app.crud import fiscal_periods_crud
from app.schemas.fiscal_periods_schemas import (
    FiscalPeriodCreate, FiscalPeriodUpdate, FiscalPeriodResponse,
)

router = APIRouter(prefix="/fiscal-periods", tags=["الفترات المحاسبية"])


@router.get("/", response_model=List[FiscalPeriodResponse], dependencies=[Depends(get_current_admin)])
def get_periods(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    period_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """قائمة الفترات"""
    return fiscal_periods_crud.get_periods(db, skip=skip, limit=limit, status=status, period_type=period_type)


@router.get("/count", dependencies=[Depends(get_current_admin)])
def get_periods_count(status: Optional[str] = None, db: Session = Depends(get_db)):
    return {"count": fiscal_periods_crud.get_periods_count(db, status=status)}


@router.get("/current", response_model=Optional[FiscalPeriodResponse], dependencies=[Depends(get_current_admin)])
def get_current_period(db: Session = Depends(get_db)):
    """الفترة الحالية"""
    return fiscal_periods_crud.get_current_period(db)


@router.get("/open", response_model=List[FiscalPeriodResponse], dependencies=[Depends(get_current_admin)])
def get_open_periods(db: Session = Depends(get_db)):
    return fiscal_periods_crud.get_open_periods(db)


@router.get("/{period_id}", response_model=FiscalPeriodResponse, dependencies=[Depends(get_current_admin)])
def get_period(period_id: int, db: Session = Depends(get_db)):
    period = fiscal_periods_crud.get_period(db, period_id)
    if not period:
        raise HTTPException(status_code=404, detail="الفترة غير موجودة")
    return period


@router.get("/{period_id}/summary", dependencies=[Depends(get_current_admin)])
def get_period_summary(period_id: int, db: Session = Depends(get_db)):
    return fiscal_periods_crud.get_period_summary(db, period_id)


@router.post("/", response_model=FiscalPeriodResponse, dependencies=[Depends(get_current_admin)])
def create_period(period: FiscalPeriodCreate, db: Session = Depends(get_db)):
    result = fiscal_periods_crud.create_period(db, period)
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/auto-create/{year}", dependencies=[Depends(get_current_admin)])
def auto_create_monthly_periods(year: int, db: Session = Depends(get_db)):
    """توليد 12 فترة شهرية تلقائيًا"""
    created = fiscal_periods_crud.auto_create_monthly_periods(db, year)
    return {"created_count": len(created), "year": year}


@router.put("/{period_id}", response_model=FiscalPeriodResponse, dependencies=[Depends(get_current_admin)])
def update_period(period_id: int, period: FiscalPeriodUpdate, db: Session = Depends(get_db)):
    result = fiscal_periods_crud.update_period(db, period_id, period)
    if result is None:
        raise HTTPException(status_code=404, detail="الفترة غير موجودة")
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/{period_id}/close", response_model=FiscalPeriodResponse, dependencies=[Depends(get_current_admin)])
def close_period(period_id: int, db: Session = Depends(get_db)):
    result = fiscal_periods_crud.close_period(db, period_id)
    if result is None:
        raise HTTPException(status_code=404, detail="الفترة غير موجودة")
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/{period_id}/reopen", response_model=FiscalPeriodResponse, dependencies=[Depends(get_current_admin)])
def reopen_period(period_id: int, db: Session = Depends(get_db)):
    result = fiscal_periods_crud.reopen_period(db, period_id)
    if result is None:
        raise HTTPException(status_code=404, detail="الفترة غير موجودة")
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/{period_id}/lock", response_model=FiscalPeriodResponse, dependencies=[Depends(get_current_admin)])
def lock_period(period_id: int, db: Session = Depends(get_db)):
    result = fiscal_periods_crud.lock_period(db, period_id)
    if result is None:
        raise HTTPException(status_code=404, detail="الفترة غير موجودة")
    return result
