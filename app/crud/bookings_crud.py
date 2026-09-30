from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from typing import List, Optional
from app.models.bookings_models import Booking, Passenger, Luggage, BookingStatus, BookingType
from app.models.trips_models import Trip
from app.schemas.bookings_schemas import BookingCreate, PassengerCreate, LuggageCreate

# ========================================
# CRUD للركاب
# ========================================
def get_passenger(db: Session, passenger_id: int):
    return db.query(Passenger).filter(Passenger.id == passenger_id).first()

def get_passengers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Passenger).offset(skip).limit(limit).all()

def create_passenger(db: Session, passenger: PassengerCreate):
    # تحديد تلقائي إذا كان رضيعاً
    is_infant = passenger.is_infant if passenger.is_infant is not None else (passenger.age is not None and passenger.age < 2)

    # استخراج customer_id و is_primary
    customer_id = getattr(passenger, "customer_id", None)
    is_primary = getattr(passenger, "is_primary", False)

    # إذا لم يُحدَّد customer_id، نحاول إيجاده بالهاتف
    if not customer_id and passenger.phone:
        from app.models.customers_models import Customer
        existing_customer = db.query(Customer).filter(Customer.phone == passenger.phone).first()
        if existing_customer:
            customer_id = existing_customer.id
            is_primary = True

    db_passenger = Passenger(
        full_name=passenger.full_name,
        phone=passenger.phone,
        email=passenger.email,
        id_number=passenger.id_number,
        age=passenger.age,
        is_infant=is_infant,
        customer_id=customer_id,
        is_primary=is_primary
    )
    db.add(db_passenger)
    db.commit()
    db.refresh(db_passenger)
    print(f" تم إنشاء راكب: {db_passenger.id} - {db_passenger.full_name} - customer_id={db_passenger.customer_id}")
    return db_passenger


def get_passenger_by_phone(db: Session, phone: str):
    return db.query(Passenger).filter(Passenger.phone == phone).first()

# ========================================
# CRUD للأمتعة
# ========================================
def get_luggage(db: Session, luggage_id: int):
    return db.query(Luggage).filter(Luggage.id == luggage_id).first()

def get_all_luggage(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Luggage).offset(skip).limit(limit).all()

def create_luggage(db: Session, luggage: LuggageCreate):
    db_luggage = Luggage(
        luggage_type=luggage.luggage_type,
        weight_kg=luggage.weight_kg,
        price=luggage.price,
        is_free=luggage.is_free,
        quantity=luggage.quantity
    )
    db.add(db_luggage)
    db.commit()
    db.refresh(db_luggage)
    return db_luggage


def update_luggage(db: Session, luggage_id: int, luggage: LuggageCreate):
    db_luggage = get_luggage(db, luggage_id)
    if not db_luggage:
        return None
    db_luggage.luggage_type = luggage.luggage_type
    db_luggage.weight_kg = luggage.weight_kg
    db_luggage.price = luggage.price
    db_luggage.is_free = luggage.is_free
    db_luggage.quantity = luggage.quantity
    db.commit()
    db.refresh(db_luggage)
    return db_luggage


def delete_luggage(db: Session, luggage_id: int):
    db_luggage = get_luggage(db, luggage_id)
    if db_luggage:
        db.delete(db_luggage)
        db.commit()
    return db_luggage

# ========================================
# CRUD للحجوزات
# ========================================
def get_booking(db: Session, booking_id: int):
    return db.query(Booking).filter(Booking.id == booking_id).first()

def get_booking_by_reference(db: Session, reference: str):
    return db.query(Booking).filter(Booking.booking_reference == reference).first()

def get_bookings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Booking).offset(skip).limit(limit).all()

def get_bookings_by_trip(db: Session, trip_id: int):
    return db.query(Booking).filter(Booking.trip_id == trip_id).all()

def get_available_seats(db: Session, trip_id: int):
    """حساب المقاعد المتاحة (الأطفال الرضع لا يحسبون)"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        return 0
    
    booked_seats = 0
    bookings = db.query(Booking).filter(
        Booking.trip_id == trip_id,
        Booking.status != BookingStatus.CANCELLED
    ).all()
    
    for booking in bookings:
        # ✅ تخطي الأطفال الرضع
        passenger = db.query(Passenger).filter(Passenger.id == booking.passenger_id).first()
        if passenger and passenger.is_infant:
            continue
        booked_seats += len(booking.seat_numbers or [])
    
    return trip.total_seats - booked_seats

def create_booking(db: Session, booking: BookingCreate):
    try:
        print(f"🔍 create_booking: trip_id={booking.trip_id}, passenger_id={booking.passenger_id}, seats={booking.seat_numbers}")
        
        # جلب الرحلة
        trip = db.query(Trip).filter(Trip.id == booking.trip_id).first()
        if not trip:
            print("❌ الرحلة غير موجودة")
            return None

        # ✅ التحقق من الوقت (ساعتان قبل الانطلاق)
        window_check = _check_departure_window(trip)
        if not window_check["allowed"]:
            print(f"❌ رُفض الحجز: {window_check['message']}")
            return None
        
        # جلب الراكب
        passenger = db.query(Passenger).filter(Passenger.id == booking.passenger_id).first()
        if not passenger:
            print("❌ الراكب غير موجود")
            return None
        
        print(f"🔍 الراكب: {passenger.full_name}, is_infant={passenger.is_infant}")
        
        # ✅ التحقق من المقاعد
        seat_count = len(booking.seat_numbers) if booking.seat_numbers else 0
        print(f"🔍 عدد المقاعد المطلوبة: {seat_count}")
        
        if not passenger.is_infant:
            if seat_count == 0:
                print("❌ البالغ يحتاج مقعداً واحداً على الأقل")
                return None
            
            available_seats = get_available_seats(db, booking.trip_id)
            print(f"🔍 المقاعد المتاحة: {available_seats}")
            if available_seats < seat_count:
                print(f"❌ لا توجد مقاعد كافية")
                return None
        
        # ✅ حساب السعر (الرضع مجاناً)
        if passenger.is_infant:
            ticket_price = 0
            print("✅ راكب رضيع → سعر التذكرة = 0")
        else:
            ticket_price = trip.price_at_time * seat_count
            print(f"✅ سعر التذكرة = {trip.price_at_time} × {seat_count} = {ticket_price}")
        
        # حساب الأمتعة
        luggage_price = 0
        luggage_items = []
        if booking.luggage_ids:
            luggage_list = db.query(Luggage).filter(Luggage.id.in_(booking.luggage_ids)).all()
            luggage_items = luggage_list
            luggage_price = sum(item.price * item.quantity for item in luggage_list)
            print(f"🔍 سعر الأمتعة: {luggage_price}")
        
        total_price = ticket_price + luggage_price
        print(f"🔍 الإجمالي: {total_price}")
        
        # توليد رقم الحجز
        import datetime as dt
        date_str = dt.datetime.now().strftime('%Y%m%d')
        last_booking = db.query(Booking).filter(
            Booking.booking_reference.like(f'BK-{date_str}-%')
        ).order_by(Booking.booking_reference.desc()).first()
        
        if last_booking:
            last_number = int(last_booking.booking_reference.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
        
        booking_reference = f'BK-{date_str}-{str(new_number).zfill(3)}'
        print(f"🔍 رقم الحجز: {booking_reference}")
        
        # ✅ تحديد الحالة
        initial_status = BookingStatus.CONFIRMED if booking.booking_type == 'office' else BookingStatus.PENDING
        print(f"🔍 الحالة: {initial_status}")
        
        # إنشاء الحجز
        db_booking = Booking(
            trip_id=booking.trip_id,
            passenger_id=booking.passenger_id,
            seat_numbers=booking.seat_numbers if booking.seat_numbers else [],
            booking_type=booking.booking_type,
            total_price=total_price,
            status=initial_status,
            booking_reference=booking_reference
        )
        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)
        print(f"✅ تم إنشاء الحجز: {db_booking.booking_reference}")
        
        # إضافة الأمتعة
        if luggage_items:
            db_booking.luggage_items = luggage_items
            db.commit()
            db.refresh(db_booking)
        
        return db_booking
        
    except Exception as e:
        db.rollback()
        import traceback
        print(f"❌ خطأ في إنشاء الحجز: {e}")
        traceback.print_exc()
        return None

def update_booking_status(db: Session, booking_id: int, status: BookingStatus):
    booking = get_booking(db, booking_id)
    if booking:
        booking.status = status
        db.commit()
        db.refresh(booking)
    return booking

def cancel_booking(db: Session, booking_id: int):
    """إلغاء حجز + تحديث إحصائيات العميل"""
    booking = update_booking_status(db, booking_id, BookingStatus.CANCELLED)
    if booking and booking.customer_id:
        from app.crud import customers_crud
        try:
            customers_crud.update_customer_stats(db, booking.customer_id)
            print(f" تحديث إحصائيات العميل {booking.customer_id}")
        except Exception as e:
            print(f"  فشل تحديث إحصائيات العميل: {e}")
    return booking

def confirm_booking(db: Session, booking_id: int):
    """تأكيد حجز + تحديث إحصائيات العميل"""
    booking = update_booking_status(db, booking_id, BookingStatus.CONFIRMED)
    if booking and booking.customer_id:
        from app.crud import customers_crud
        try:
            customers_crud.update_customer_stats(db, booking.customer_id)
            print(f" تحديث إحصائيات العميل {booking.customer_id}")
        except Exception as e:
            print(f"  فشل تحديث إحصائيات العميل: {e}")
    return booking

def get_booking_by_passenger(db: Session, passenger_id: int):
    return db.query(Booking).filter(Booking.passenger_id == passenger_id).all()
def get_booked_seat_numbers(db: Session, trip_id: int):
    """إرجاع قائمة بأرقام المقاعد المحجوزة فعلياً"""
    bookings = db.query(Booking).filter(
        Booking.trip_id == trip_id,
        Booking.status != BookingStatus.CANCELLED
    ).all()
    
    booked_seats = []
    for booking in bookings:
        # تخطي الأطفال الرضع (لا يحجزون مقاعد)
        passenger = db.query(Passenger).filter(Passenger.id == booking.passenger_id).first()
        if passenger and passenger.is_infant:
            continue
        if booking.seat_numbers:
            booked_seats.extend(booking.seat_numbers)
    
    return booked_seats

# ============================================================
# ✅ Group Booking (PNR) - الحجز الجماعي
# ============================================================

def _generate_pnr(db: Session) -> str:
    """توليد رقم PNR فريد — صيغة: GRP-YYYYMMDD-NNN"""
    import datetime as dt
    date_str = dt.datetime.now().strftime('%Y%m%d')

    # ابحث عن آخر PNR في نفس اليوم
    last = db.query(Booking).filter(
        Booking.pnr_reference.like(f'GRP-{date_str}-%')
    ).order_by(Booking.pnr_reference.desc()).first()

    if last and last.pnr_reference:
        try:
            last_num = int(last.pnr_reference.split('-')[-1])
            new_num = last_num + 1
        except (ValueError, IndexError):
            new_num = 1
    else:
        new_num = 1

    return f'GRP-{date_str}-{str(new_num).zfill(3)}'


def _generate_ticket_numbers(db: Session, count: int) -> list:
    """توليد عدد من أرقام التذاكر الفريدة — TKT-YYYYMMDD-NNNN"""
    import datetime as dt
    date_str = dt.datetime.now().strftime('%Y%m%d')

    # ابحث عن آخر رقم تذكرة في نفس اليوم
    last = db.query(Booking).filter(
        Booking.ticket_number.like(f'TKT-{date_str}-%')
    ).order_by(Booking.ticket_number.desc()).first()

    if last and last.ticket_number:
        try:
            last_num = int(last.ticket_number.split('-')[-1])
        except (ValueError, IndexError):
            last_num = 0
    else:
        last_num = 0

    tickets = []
    for i in range(count):
        tickets.append(f'TKT-{date_str}-{str(last_num + i + 1).zfill(4)}')
    return tickets


def _check_departure_window(trip) -> dict:
    """
    التحقق من أن الرحلة ليست على وشك الانطلاق.
    ✅ قاعدة: يجب أن يتبقى ساعتان على الأقل قبل وقت المغادرة.
    
    Returns:
        dict مع:
        - allowed: bool
        - minutes_left: عدد الدقائق المتبقية
        - message: رسالة مفصلة
    """
    from datetime import datetime, timezone
    from decimal import Decimal

    if not trip or not trip.departure_time:
        return {"allowed": False, "minutes_left": 0, "message": "بيانات الرحلة غير متوفرة"}

    # استخدام UTC للمقارنة (لأن التواريخ مخزنة بـ timezone)
    now = datetime.now(timezone.utc)

    # تأكد أن departure_time له timezone
    dep_time = trip.departure_time
    if dep_time.tzinfo is None:
        dep_time = dep_time.replace(tzinfo=timezone.utc)

    # الفرق الزمني
    time_left = dep_time - now
    minutes_left = int(time_left.total_seconds() / 60)

    # الحد الأدنى: 120 دقيقة (ساعتان)
    MIN_MINUTES = 120

    if minutes_left < MIN_MINUTES:
        if minutes_left <= 0:
            msg = "انطلقت هذه الرحلة بالفعل — لا يمكن الحجز"
        elif minutes_left < 60:
            msg = f"لم يتبقَّ سوى {minutes_left} دقيقة على انطلاق الرحلة — يجب التواصل مع مكتب الحجز"
        else:
            hours = minutes_left // 60
            mins = minutes_left % 60
            msg = f"لم يتبقَّ سوى {hours} ساعة و {mins} دقيقة على انطلاق الرحلة — يجب التواصل مع مكتب الحجز"

        return {"allowed": False, "minutes_left": minutes_left, "message": msg}

    return {"allowed": True, "minutes_left": minutes_left, "message": ""}


def create_booking_group(db: Session, group_data):
    """
    إنشاء مجموعة حجز كاملة (عائلة) برقم PNR موحد.
    + ربط بـ customer + branch تلقائيًا
    """
    import datetime as dt
    from decimal import Decimal
    from app.models.bookings_models import Booking, Passenger, Luggage, BookingStatus
    from app.crud import customers_crud

    # 1) جلب الرحلة
    trip = db.query(Trip).filter(Trip.id == group_data.trip_id).first()
    if not trip:
        print(f" الرحلة غير موجودة: {group_data.trip_id}")
        return None

    #  التحقق من الوقت (ساعتان قبل الانطلاق)
    window_check = _check_departure_window(trip)
    if not window_check["allowed"]:
        print(f" رُفض الحجز: {window_check['message']}")
        return {
            "error": True,
            "error_type": "booking_window_closed",
            "message": window_check["message"],
            "minutes_left": window_check["minutes_left"],
        }

    # 2) التحقق من كل الركاب والمقاعد
    total_seats_requested = 0
    parsed_items = []

    for item in group_data.items:
        passenger = db.query(Passenger).filter(Passenger.id == item.passenger_id).first()
        if not passenger:
            print(f" الراكب غير موجود: {item.passenger_id}")
            return None

        seats = item.seat_numbers or []
        if not passenger.is_infant:
            if len(seats) == 0:
                print(f" الراكب {passenger.full_name} يحتاج مقعداً")
                return None
            total_seats_requested += len(seats)

        #  تجميع الكميات
        luggage_items = []
        if item.luggage_ids:
            luggage_quantities = {}
            for lid in item.luggage_ids:
                luggage_quantities[lid] = luggage_quantities.get(lid, 0) + 1
            
            for lid, qty in luggage_quantities.items():
                l = db.query(Luggage).filter(Luggage.id == lid).first()
                if l:
                    luggage_items.append({"luggage": l, "quantity": qty})

        parsed_items.append({
            "passenger": passenger,
            "seats": seats,
            "luggage": luggage_items,
        })

    # 3) التحقق من المقاعد المتاحة
    available = get_available_seats(db, group_data.trip_id)
    if available < total_seats_requested:
        print(f" لا توجد مقاعد كافية. المتاح: {available}, المطلوب: {total_seats_requested}")
        return None

    #  4) جلب/إنشاء العميل  من الراكب الأساسي (الأول)
    customer = None
    primary_passenger = parsed_items[0]["passenger"] if parsed_items else None

    if primary_passenger and primary_passenger.phone:
        try:
            customer = customers_crud.get_or_create_customer(
                db,
                full_name=primary_passenger.full_name,
                phone=primary_passenger.phone,
                email=primary_passenger.email,
            )
            if customer and not isinstance(customer, dict):
                print(f" العميل: {customer.customer_code}  {customer.full_name}")
            else:
                customer = None
        except Exception as e:
            print(f"  فشل جلب/إنشاء العميل: {e}")
            customer = None

    #  5) جلب فرع انطلاق الرحلة
    branch_id = None
    if trip.branch_id:
        branch_id = trip.branch_id
        print(f" الفرع: {branch_id}")
    else:
        # إذا الرحلة ليس لها فرع، نستخدم الفرع الرئيسي
        from app.models.branches_models import Branch
        main_branch = db.query(Branch).filter(Branch.code == "BR-001").first()
        if main_branch:
            branch_id = main_branch.id
            print(f" الفرع الرئيسي: {main_branch.name}")

    # 6) توليد PNR وأرقام التذاكر
    try:
        pnr = _generate_pnr(db)
        tickets = _generate_ticket_numbers(db, len(parsed_items))
        print(f" PNR: {pnr}")
        print(f" Tickets: {tickets}")
    except Exception as e:
        print(f" فشل توليد الأرقام: {e}")
        return None

    # 7) إنشاء الحجوزات
    created_bookings = []
    total_price = Decimal("0")

    try:
        for idx, parsed in enumerate(parsed_items):
            passenger = parsed["passenger"]
            seats = parsed["seats"]
            luggage_items = parsed["luggage"]

            # سعر التذكرة
            if passenger.is_infant:
                ticket_price = Decimal("0")
            else:
                ticket_price = Decimal(str(trip.price_at_time)) * len(seats)

            # سعر الأمتعة (مع الكميات)
            luggage_price = Decimal("0")
            for li in luggage_items:
                if isinstance(li, dict):
                    luggage_price += Decimal(str(li["luggage"].price)) * li["quantity"]
                else:
                    luggage_price += Decimal(str(li.price)) * getattr(li, "quantity", 1)

            item_total = ticket_price + luggage_price
            total_price += item_total

            # رقم حجز فردي
            date_str = dt.datetime.now().strftime('%Y%m%d')
            last_booking = db.query(Booking).filter(
                Booking.booking_reference.like(f'BK-{date_str}-%')
            ).order_by(Booking.booking_reference.desc()).first()

            if last_booking:
                try:
                    last_num = int(last_booking.booking_reference.split('-')[-1])
                except (ValueError, IndexError):
                    last_num = 0
            else:
                last_num = 0
            booking_ref = f'BK-{date_str}-{str(last_num + 1).zfill(3)}'

            # حالة الحجز
            initial_status = BookingStatus.CONFIRMED if group_data.booking_type == 'office' else BookingStatus.PENDING

            #  إنشاء الحجز مع customer_id + branch_id
            new_booking = Booking(
                trip_id=group_data.trip_id,
                passenger_id=passenger.id,
                seat_numbers=seats if seats else [],
                booking_type=group_data.booking_type,
                total_price=item_total,
                status=initial_status,
                booking_reference=booking_ref,
                pnr_reference=pnr,
                ticket_number=tickets[idx],
                #  الربط الجديد
                customer_id=customer.id if customer else None,
                branch_id=branch_id,
                booking_source='online' if group_data.booking_type == 'online' else 'office',
            )
            db.add(new_booking)
            db.flush()

            # ربط الأمتعة (مع الكميات)
            if luggage_items:
                from app.models.bookings_models import BookingLuggage
                for li in luggage_items:
                    if isinstance(li, dict):
                        assoc = BookingLuggage(
                            booking_id=new_booking.id,
                            luggage_id=li["luggage"].id,
                            quantity=li["quantity"]
                        )
                        db.add(assoc)
                    else:
                        # للتوافق مع الكود القديم
                        assoc = BookingLuggage(
                            booking_id=new_booking.id,
                            luggage_id=li.id,
                            quantity=1
                        )
                        db.add(assoc)

            #  ربط الراكب بالعميل
            if customer:
                passenger.customer_id = customer.id
                passenger.is_primary = (idx == 0)

            created_bookings.append(new_booking)

        db.commit()

        for b in created_bookings:
            db.refresh(b)

        print(f" تم إنشاء {len(created_bookings)} حجز تحت PNR: {pnr}")
        if customer:
            print(f"    العميل: {customer.customer_code}  {customer.full_name}")
        if branch_id:
            print(f"    الفرع: {branch_id}")

        #  تحديث إحصائيات العميل
        if customer:
            try:
                customers_crud.update_customer_stats(db, customer.id)
            except Exception as e:
                print(f"  فشل تحديث إحصائيات العميل: {e}")

        return {
            "pnr_reference": pnr,
            "total_price": total_price,
            "bookings_count": len(created_bookings),
            "bookings": created_bookings,
        }

    except Exception as e:
        db.rollback()
        import traceback
        print(f" خطأ في إنشاء الحجز الجماعي: {e}")
        traceback.print_exc()
        return None

def get_bookings_by_pnr(db: Session, pnr: str):
    """جلب كل حجوزات مجموعة معينة"""
    return db.query(Booking).filter(Booking.pnr_reference == pnr).all()
