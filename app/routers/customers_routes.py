from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.database import get_db
from app.routers.auth_routes import get_current_admin
from app.crud import customers_crud
from app.schemas.customers_schemas import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerSimple,
)

router = APIRouter(prefix="/customers", tags=["العملاء"])


# 
# قراءة (محمي)
# 

@router.get("/", response_model=List[CustomerResponse], dependencies=[Depends(get_current_admin)])
def get_customers(
    skip: int = 0,
    limit: int = 100,
    is_vip: Optional[bool] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """قائمة العملاء"""
    return customers_crud.get_customers(
        db, skip=skip, limit=limit, is_vip=is_vip, is_active=is_active
    )


@router.get("/count", dependencies=[Depends(get_current_admin)])
def get_customers_count(
    is_vip: Optional[bool] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """عدد العملاء"""
    return {"count": customers_crud.get_customers_count(db, is_vip=is_vip, is_active=is_active)}


@router.get("/phone/{phone}", response_model=CustomerResponse, dependencies=[Depends(get_current_admin)])
def get_customer_by_phone(phone: str, db: Session = Depends(get_db)):
    """جلب عميل بالهاتف"""
    customer = customers_crud.get_customer_by_phone(db, phone)
    if not customer:
        raise HTTPException(status_code=404, detail="العميل غير موجود")
    return customer


@router.get("/{customer_id}", response_model=CustomerResponse, dependencies=[Depends(get_current_admin)])
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """جلب عميل بالمعرف"""
    customer = customers_crud.get_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="العميل غير موجود")
    return customer


# 
# إنشاء / تعديل / حذف
# 

@router.post("/", response_model=CustomerResponse, dependencies=[Depends(get_current_admin)])
def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    """إنشاء عميل جديد"""
    result = customers_crud.create_customer(db, customer)
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/get-or-create", response_model=CustomerResponse)
def get_or_create_customer(
    full_name: str,
    phone: str,
    email: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """جلب أو إنشاء عميل  للاستخدام من الحجز الذاتي (عام)"""
    customer = customers_crud.get_or_create_customer(
        db, full_name=full_name, phone=phone, email=email
    )
    if isinstance(customer, dict) and customer.get("error"):
        raise HTTPException(status_code=400, detail=customer["message"])
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse, dependencies=[Depends(get_current_admin)])
def update_customer(customer_id: int, customer: CustomerUpdate, db: Session = Depends(get_db)):
    """تعديل عميل"""
    result = customers_crud.update_customer(db, customer_id, customer)
    if result is None:
        raise HTTPException(status_code=404, detail="العميل غير موجود")
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.delete("/{customer_id}", dependencies=[Depends(get_current_admin)])
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    """حذف منطقي  تعطيل العميل"""
    result = customers_crud.delete_customer(db, customer_id)
    if not result:
        raise HTTPException(status_code=404, detail="العميل غير موجود")
    return {"message": f"تم تعطيل العميل '{result.full_name}' بنجاح"}


@router.post("/{customer_id}/refresh-stats", dependencies=[Depends(get_current_admin)])
def refresh_customer_stats(customer_id: int, db: Session = Depends(get_db)):
    """تحديث إحصائيات العميل"""
    result = customers_crud.update_customer_stats(db, customer_id)
    if not result:
        raise HTTPException(status_code=404, detail="العميل غير موجود")
    return {"message": "تم تحديث الإحصائيات", "customer_id": customer_id}
