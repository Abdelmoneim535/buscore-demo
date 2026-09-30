from sqlalchemy.orm import Session
from datetime import datetime
from app.models.payments_models import Payment, PaymentStatus
from app.models.bookings_models import Booking, BookingStatus
from app.schemas.payments_schemas import PaymentCreate

def get_payment(db: Session, payment_id: int):
    return db.query(Payment).filter(Payment.id == payment_id).first()

def get_payment_by_booking(db: Session, booking_id: int):
    return db.query(Payment).filter(Payment.booking_id == booking_id).first()

def get_all_payments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Payment).offset(skip).limit(limit).all()

def create_payment(db: Session, payment: PaymentCreate):
    booking = db.query(Booking).filter(Booking.id == payment.booking_id).first()
    if not booking:
        return None
    existing = get_payment_by_booking(db, payment.booking_id)
    if existing:
        return None
    db_payment = Payment(
        booking_id=payment.booking_id,
        amount=payment.amount,
        payment_method=payment.payment_method,
        status=PaymentStatus.PENDING,
        transaction_id=payment.transaction_id
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

def update_payment_status(db: Session, payment_id: int, status: PaymentStatus, transaction_id: str = None):
    payment = get_payment(db, payment_id)
    if not payment:
        return None
    payment.status = status
    if transaction_id:
        payment.transaction_id = transaction_id
    if status == PaymentStatus.COMPLETED:
        payment.paid_at = datetime.now()
        booking = db.query(Booking).filter(Booking.id == payment.booking_id).first()
        if booking:
            booking.status = BookingStatus.CONFIRMED
            db.add(booking)
    if status in [PaymentStatus.FAILED, PaymentStatus.REFUNDED]:
        booking = db.query(Booking).filter(Booking.id == payment.booking_id).first()
        if booking:
            booking.status = BookingStatus.CANCELLED
            db.add(booking)
    db.commit()
    db.refresh(payment)
    return payment

def complete_payment(db: Session, payment_id: int, transaction_id: str = None):
    return update_payment_status(db, payment_id, PaymentStatus.COMPLETED, transaction_id)

def fail_payment(db: Session, payment_id: int, transaction_id: str = None):
    return update_payment_status(db, payment_id, PaymentStatus.FAILED, transaction_id)

def refund_payment(db: Session, payment_id: int):
    return update_payment_status(db, payment_id, PaymentStatus.REFUNDED)