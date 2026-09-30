from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone
from decimal import Decimal
from app.models.customers_models import Customer
from app.schemas.customers_schemas import CustomerCreate, CustomerUpdate


# 
# قراءة
# 

def get_customer(db: Session, customer_id: int):
    """جلب عميل بالمعرف"""
    return db.query(Customer).filter(Customer.id == customer_id).first()


def get_customer_by_phone(db: Session, phone: str):
    """جلب عميل بالهاتف (فريد)"""
    return db.query(Customer).filter(Customer.phone == phone).first()


def get_customers(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    is_vip: Optional[bool] = None,
    is_active: Optional[bool] = None,
) -> List[Customer]:
    """قائمة العملاء مع إمكانية الفلترة"""
    query = db.query(Customer)
    if is_vip is not None:
        query = query.filter(Customer.is_vip == is_vip)
    if is_active is not None:
        query = query.filter(Customer.is_active == is_active)
    return query.order_by(Customer.id.desc()).offset(skip).limit(limit).all()


def get_customers_count(
    db: Session,
    is_vip: Optional[bool] = None,
    is_active: Optional[bool] = None,
) -> int:
    """عدد العملاء"""
    query = db.query(Customer)
    if is_vip is not None:
        query = query.filter(Customer.is_vip == is_vip)
    if is_active is not None:
        query = query.filter(Customer.is_active == is_active)
    return query.count()


# 
# إنشاء
# 

def create_customer(db: Session, customer: CustomerCreate):
    """إنشاء عميل جديد"""
    # التحقق من رقم الهاتف (فريد)
    existing = db.query(Customer).filter(Customer.phone == customer.phone).first()
    if existing:
        return {
            "error": "phone_duplicate",
            "message": f"رقم الهاتف '{customer.phone}' مستخدم مسبقا للعميل: {existing.full_name}",
        }

    # توليد كود فريد
    code = _generate_customer_code(db)

    db_customer = Customer(
        customer_code=code,
        full_name=customer.full_name,
        phone=customer.phone,
        phone_secondary=customer.phone_secondary,
        email=customer.email,
        id_number=customer.id_number,
        passport_number=customer.passport_number,
        national_id=customer.national_id,
        birth_date=customer.birth_date,
        nationality=customer.nationality,
        preferred_branch_id=customer.preferred_branch_id,
        is_vip=customer.is_vip if customer.is_vip is not None else False,
        is_active=customer.is_active if customer.is_active is not None else True,
        notes=customer.notes,
    )
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer


def _generate_customer_code(db: Session) -> str:
    """توليد كود فريد للعميل: CUST-000001"""
    last = db.query(Customer).filter(
        Customer.customer_code.like("CUST-%")
    ).order_by(Customer.customer_code.desc()).first()

    if last and last.customer_code:
        try:
            last_num = int(last.customer_code.split("-")[-1])
            new_num = last_num + 1
        except (ValueError, IndexError):
            new_num = 1
    else:
        new_num = 1

    return f"CUST-{str(new_num).zfill(6)}"


def find_customer_by_identifiers(
    db: Session,
    phone: Optional[str] = None,
    phone_secondary: Optional[str] = None,
    passport_number: Optional[str] = None,
    national_id: Optional[str] = None,
):
    """
    بحث ذكي عن عميل بـ 4 طرق:
    1) الهاتف الأساسي
    2) الهاتف الثانوي
    3) رقم الجواز
    4) الرقم الوطني
    """
    from sqlalchemy import or_

    filters = []
    if phone:
        filters.append(Customer.phone == phone)
    if phone_secondary:
        filters.append(Customer.phone_secondary == phone_secondary)
    if passport_number:
        filters.append(Customer.passport_number == passport_number)
    if national_id:
        filters.append(Customer.national_id == national_id)

    if not filters:
        return None

    return db.query(Customer).filter(or_(*filters)).first()


def search_customers(db: Session, query: str, limit: int = 10):
    """بحث شامل  بالاسم أو الهاتف أو الإثبات"""
    from sqlalchemy import or_

    if not query or len(query.strip()) < 2:
        return []

    q = query.strip()
    return db.query(Customer).filter(
        or_(
            Customer.full_name.ilike(f"%{q}%"),
            Customer.phone.ilike(f"%{q}%"),
            Customer.phone_secondary.ilike(f"%{q}%"),
            Customer.passport_number.ilike(f"%{q}%"),
            Customer.national_id.ilike(f"%{q}%"),
            Customer.email.ilike(f"%{q}%"),
        )
    ).limit(limit).all()


def get_or_create_customer(
    db: Session,
    full_name: str,
    phone: str,
    email: Optional[str] = None,
    phone_secondary: Optional[str] = None,
    passport_number: Optional[str] = None,
    national_id: Optional[str] = None,
):
    """
    جلب أو إنشاء عميل  بحث ذكي بـ 4 طرق
    - إذا وُجد  يُحدّث معلوماته إن لزم
    - إذا لم يوجد  يُنشئ عميل جديد بكود CUST-XXXXXX
    """
    # البحث الذكي
    customer = find_customer_by_identifiers(
        db,
        phone=phone,
        phone_secondary=phone_secondary,
        passport_number=passport_number,
        national_id=national_id,
    )

    if customer:
        # تحديث البيانات إن لزم
        updated = False
        if phone and not customer.phone:
            customer.phone = phone
            updated = True
        if phone_secondary and not customer.phone_secondary:
            customer.phone_secondary = phone_secondary
            updated = True
        if passport_number and not customer.passport_number:
            customer.passport_number = passport_number
            updated = True
        if national_id and not customer.national_id:
            customer.national_id = national_id
            updated = True
        if email and not customer.email:
            customer.email = email
            updated = True

        if updated:
            db.commit()
            db.refresh(customer)

        return customer

    # إنشاء عميل جديد
    code = _generate_customer_code(db)
    db_customer = Customer(
        customer_code=code,
        full_name=full_name,
        phone=phone,
        phone_secondary=phone_secondary,
        email=email,
        passport_number=passport_number,
        national_id=national_id,
    )
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer


# 
# تعديل
# 

def update_customer(db: Session, customer_id: int, customer: CustomerUpdate):
    """تعديل عميل"""
    db_customer = get_customer(db, customer_id)
    if not db_customer:
        return None

    update_data = customer.model_dump(exclude_unset=True)

    # التحقق من الهاتف إذا تم تغييره
    if "phone" in update_data and update_data["phone"] != db_customer.phone:
        existing = db.query(Customer).filter(
            Customer.phone == update_data["phone"],
            Customer.id != customer_id,
        ).first()
        if existing:
            return {
                "error": "phone_duplicate",
                "message": f"رقم الهاتف '{update_data['phone']}' مستخدم مسبقا",
            }

    for key, value in update_data.items():
        setattr(db_customer, key, value)

    db.commit()
    db.refresh(db_customer)
    return db_customer


# 
# حذف
# 

def delete_customer(db: Session, customer_id: int):
    """حذف منطقي  تعطيل العميل"""
    db_customer = get_customer(db, customer_id)
    if not db_customer:
        return None

    db_customer.is_active = False
    db.commit()
    db.refresh(db_customer)
    return db_customer


# 
# إحصائيات
# 

def update_customer_stats(db: Session, customer_id: int):
    """
    تحديث إحصائيات العميل
    - total_bookings: عدد الحجوزات (PNR فريدة)
    - total_tickets: عدد التذاكر (كل passenger بتذكرة)
    - total_spent: إجمالي الإنفاق
    - total_infants: عدد الرضع
    """
    from app.models.bookings_models import Booking, BookingStatus, Passenger
    from sqlalchemy import func, distinct

    customer = get_customer(db, customer_id)
    if not customer:
        return None

    # عدد الحجوزات (PNR فريدة غير ملغاة)
    total_bookings = db.query(
        func.count(distinct(Booking.pnr_reference))
    ).filter(
        Booking.customer_id == customer_id,
        Booking.status != BookingStatus.CANCELLED,
    ).scalar() or 0

    # إجمالي التذاكر (كل Booking بـ passenger غير رضيع)
    all_bookings = db.query(Booking).filter(
        Booking.customer_id == customer_id,
        Booking.status != BookingStatus.CANCELLED,
    ).all()

    total_tickets = 0
    total_infants = 0

    for b in all_bookings:
        passenger = db.query(Passenger).filter(Passenger.id == b.passenger_id).first()
        if passenger and passenger.is_infant:
            total_infants += 1
        else:
            total_tickets += 1

    # إجمالي الإنفاق (المؤكدة فقط)
    total_spent = db.query(func.sum(Booking.total_price)).filter(
        Booking.customer_id == customer_id,
        Booking.status == BookingStatus.CONFIRMED,
    ).scalar() or Decimal("0")

    customer.total_bookings = total_bookings
    customer.total_tickets = total_tickets
    customer.total_infants = total_infants
    customer.total_spent = total_spent
    customer.last_booking_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(customer)
    return customer
