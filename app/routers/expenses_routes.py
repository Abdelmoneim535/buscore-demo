from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database.database import get_db
from app.routers.auth_routes import get_current_admin
from app.crud import expenses_crud
from app.schemas.expenses_schemas import (
    ExpenseCategoryCreate, ExpenseCategoryResponse,
    ExpenseCreate, ExpenseResponse,
    FinancialSummary, FinancialReport,
)

router = APIRouter(prefix="/expenses", tags=["المحاسبة"])


# ============================================================
# التصنيفات
# ============================================================

@router.get("/categories", response_model=List[ExpenseCategoryResponse], dependencies=[Depends(get_current_admin)])
def get_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return expenses_crud.get_categories(db, skip=skip, limit=limit)


@router.post("/categories", response_model=ExpenseCategoryResponse, dependencies=[Depends(get_current_admin)])
def create_category(category: ExpenseCategoryCreate, db: Session = Depends(get_db)):
    result = expenses_crud.create_category(db, category)
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.put("/categories/{category_id}", response_model=ExpenseCategoryResponse, dependencies=[Depends(get_current_admin)])
def update_category(category_id: int, category: ExpenseCategoryCreate, db: Session = Depends(get_db)):
    updated = expenses_crud.update_category(db, category_id, category)
    if not updated:
        raise HTTPException(status_code=404, detail="التصنيف غير موجود")
    return updated


@router.delete("/categories/{category_id}", dependencies=[Depends(get_current_admin)])
def delete_category(category_id: int, db: Session = Depends(get_db)):
    result = expenses_crud.delete_category(db, category_id)
    if not result:
        raise HTTPException(status_code=404, detail="التصنيف غير موجود")
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"message": "تم حذف التصنيف بنجاح"}


# ============================================================
# المصروفات
# ============================================================

@router.get("/", response_model=List[ExpenseResponse], dependencies=[Depends(get_current_admin)])
def get_expenses(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = Query(None),
    bus_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    return expenses_crud.get_expenses(
        db,
        skip=skip,
        limit=limit,
        category_id=category_id,
        bus_id=bus_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.post("/", response_model=ExpenseResponse, dependencies=[Depends(get_current_admin)])
def create_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    # التحقق من وجود التصنيف
    cat = expenses_crud.get_category(db, expense.category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="التصنيف غير موجود")
    return expenses_crud.create_expense(db, expense)


@router.get("/{expense_id}", response_model=ExpenseResponse, dependencies=[Depends(get_current_admin)])
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    exp = expenses_crud.get_expense(db, expense_id)
    if not exp:
        raise HTTPException(status_code=404, detail="المصروف غير موجود")
    return exp


@router.put("/{expense_id}", response_model=ExpenseResponse, dependencies=[Depends(get_current_admin)])
def update_expense(expense_id: int, expense: ExpenseCreate, db: Session = Depends(get_db)):
    updated = expenses_crud.update_expense(db, expense_id, expense)
    if not updated:
        raise HTTPException(status_code=404, detail="المصروف غير موجود")
    return updated


@router.delete("/{expense_id}", dependencies=[Depends(get_current_admin)])
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    deleted = expenses_crud.delete_expense(db, expense_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="المصروف غير موجود")
    return {"message": f"تم حذف المصروف رقم {expense_id} بنجاح"}


# ============================================================
# التقارير المالية
# ============================================================

@router.get("/reports/summary", response_model=FinancialSummary, dependencies=[Depends(get_current_admin)])
def get_summary(
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    db: Session = Depends(get_db),
):
    return expenses_crud.get_financial_summary(db, date_from, date_to)


@router.get("/reports/full", response_model=FinancialReport, dependencies=[Depends(get_current_admin)])
def get_full_report(
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    db: Session = Depends(get_db),
):
    return expenses_crud.get_full_financial_report(db, date_from, date_to)