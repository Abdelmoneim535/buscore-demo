from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database.database import get_db
from app.routers.auth_routes import get_current_admin
from app.crud import payments_crud
from app.models.bookings_models import Booking
from app.schemas.payments_schemas import PaymentCreate, PaymentResponse, PaymentUpdateStatus

router = APIRouter(prefix="/payments", tags=["المدفوعات"])

@router.get("/", response_model=List[PaymentResponse], dependencies=[Depends(get_current_admin)])
def get_all_payments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return payments_crud.get_all_payments(db, skip=skip, limit=limit)

@router.get("/{payment_id}", response_model=PaymentResponse, dependencies=[Depends(get_current_admin)])
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    payment = payments_crud.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="الدفعة غير موجودة")
    return payment

@router.get("/booking/{booking_id}", response_model=PaymentResponse, dependencies=[Depends(get_current_admin)])
def get_payment_by_booking(booking_id: int, db: Session = Depends(get_db)):
    payment = payments_crud.get_payment_by_booking(db, booking_id)
    if not payment:
        raise HTTPException(status_code=404, detail="لا توجد دفعة لهذا الحجز")
    return payment

@router.post("/", response_model=PaymentResponse, dependencies=[Depends(get_current_admin)])
def create_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == payment.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="الحجز غير موجود")
    existing = payments_crud.get_payment_by_booking(db, payment.booking_id)
    if existing:
        raise HTTPException(status_code=400, detail="يوجد دفعة سابقة لهذا الحجز")
    new_payment = payments_crud.create_payment(db, payment)
    if not new_payment:
        raise HTTPException(status_code=400, detail="فشل إنشاء الدفعة")
    return new_payment

@router.patch("/{payment_id}/status", dependencies=[Depends(get_current_admin)])
def update_payment_status(payment_id: int, status_update: PaymentUpdateStatus, db: Session = Depends(get_db)):
    payment = payments_crud.update_payment_status(db, payment_id, status_update.status, status_update.transaction_id)
    if not payment:
        raise HTTPException(status_code=404, detail="الدفعة غير موجودة")
    return {"message": f"تم تحديث حالة الدفعة إلى {status_update.status.value}", "payment_id": payment.id, "status": payment.status.value}

@router.post("/{payment_id}/complete", dependencies=[Depends(get_current_admin)])
def complete_payment(payment_id: int, transaction_id: str, db: Session = Depends(get_db)):
    payment = payments_crud.complete_payment(db, payment_id, transaction_id)
    if not payment:
        raise HTTPException(status_code=404, detail="الدفعة غير موجودة")
    return {"message": "تم تأكيد الدفع بنجاح", "payment_id": payment.id, "status": payment.status.value, "booking_reference": payment.booking.booking_reference}

@router.post("/{payment_id}/fail", dependencies=[Depends(get_current_admin)])
def fail_payment(payment_id: int, transaction_id: str = None, db: Session = Depends(get_db)):
    payment = payments_crud.fail_payment(db, payment_id, transaction_id)
    if not payment:
        raise HTTPException(status_code=404, detail="الدفعة غير موجودة")
    return {"message": "تم تسجيل فشل الدفع", "payment_id": payment.id, "status": payment.status.value}

@router.post("/{payment_id}/refund", dependencies=[Depends(get_current_admin)])
def refund_payment(payment_id: int, db: Session = Depends(get_db)):
    payment = payments_crud.refund_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="الدفعة غير موجودة")
    return {"message": "تم استرجاع المبلغ بنجاح", "payment_id": payment.id, "status": payment.status.value}