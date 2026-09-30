from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database.database import get_db
from app.routers.auth_routes import get_current_admin
from app.crud import employees_crud
from app.schemas.employees_schemas import (
    EmployeeCreate, EmployeeResponse,
    EmployeeTransactionCreate, EmployeeTransactionResponse,
    EmployeeStatement,
)

router = APIRouter(prefix="/employees", tags=["العاملون والرواتب"])


# ============================================================
# العاملون
# ============================================================

@router.get("/", response_model=List[EmployeeResponse], dependencies=[Depends(get_current_admin)])
def get_employees(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = Query(False),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    return employees_crud.get_employees(db, skip=skip, limit=limit, active_only=active_only, search=search)


@router.post("/", response_model=EmployeeResponse, dependencies=[Depends(get_current_admin)])
def create_employee(emp: EmployeeCreate, db: Session = Depends(get_db)):
    return employees_crud.create_employee(db, emp)


@router.get("/{employee_id}", response_model=EmployeeResponse, dependencies=[Depends(get_current_admin)])
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    emp = employees_crud.get_employee(db, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="الموظف غير موجود")
    return emp


@router.put("/{employee_id}", response_model=EmployeeResponse, dependencies=[Depends(get_current_admin)])
def update_employee(employee_id: int, emp: EmployeeCreate, db: Session = Depends(get_db)):
    updated = employees_crud.update_employee(db, employee_id, emp)
    if not updated:
        raise HTTPException(status_code=404, detail="الموظف غير موجود")
    return updated


@router.delete("/{employee_id}", dependencies=[Depends(get_current_admin)])
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    deleted = employees_crud.delete_employee(db, employee_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="الموظف غير موجود")
    return {"message": f"تم حذف الموظف {deleted.full_name} بنجاح"}


# ============================================================
# الحركات المالية
# ============================================================

@router.get("/transactions/all", response_model=List[EmployeeTransactionResponse], dependencies=[Depends(get_current_admin)])
def get_all_transactions(
    employee_id: Optional[int] = Query(None),
    transaction_type: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    return employees_crud.get_transactions(
        db,
        employee_id=employee_id,
        transaction_type=transaction_type,
        date_from=date_from,
        date_to=date_to,
    )


@router.post("/transactions", response_model=EmployeeTransactionResponse, dependencies=[Depends(get_current_admin)])
def create_transaction(txn: EmployeeTransactionCreate, db: Session = Depends(get_db)):
    emp = employees_crud.get_employee(db, txn.employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="الموظف غير موجود")

    if txn.transaction_type not in ("salary", "advance", "deduction", "bonus"):
        raise HTTPException(status_code=400, detail="نوع الحركة غير صحيح")

    result = employees_crud.create_transaction(db, txn)
    if not result:
        raise HTTPException(status_code=400, detail="فشل إنشاء الحركة")
    return result


@router.put("/transactions/{transaction_id}", response_model=EmployeeTransactionResponse, dependencies=[Depends(get_current_admin)])
def update_transaction(transaction_id: int, txn: EmployeeTransactionCreate, db: Session = Depends(get_db)):
    updated = employees_crud.update_transaction(db, transaction_id, txn)
    if not updated:
        raise HTTPException(status_code=404, detail="الحركة غير موجودة")
    return updated


@router.delete("/transactions/{transaction_id}", dependencies=[Depends(get_current_admin)])
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    deleted = employees_crud.delete_transaction(db, transaction_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="الحركة غير موجودة")
    return {"message": "تم حذف الحركة بنجاح"}


# ============================================================
# كشف حساب موظف
# ============================================================

@router.get("/{employee_id}/statement", response_model=EmployeeStatement, dependencies=[Depends(get_current_admin)])
def get_statement(employee_id: int, db: Session = Depends(get_db)):
    statement = employees_crud.get_employee_statement(db, employee_id)
    if not statement:
        raise HTTPException(status_code=404, detail="الموظف غير موجود")
    return statement
