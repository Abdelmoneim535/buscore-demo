from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.trips_models import Route, PricingHistory, Trip
from app.models.bus_models import Bus
from app.schemas.trips_schemas import RouteCreate, PricingHistoryCreate, TripCreate
from datetime import datetime
from datetime import timedelta  

def _to_aware(dt):
    """تحويل أي datetime إلى timezone-aware (UTC)"""
    from datetime import timezone
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

def get_route(db: Session, route_id: int):
    return db.query(Route).filter(Route.id == route_id).first()

def get_route_by_code(db: Session, code: str):
    return db.query(Route).filter(Route.code == code).first()

def get_routes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Route).offset(skip).limit(limit).all()

def create_route(db: Session, route: RouteCreate):
    existing = get_route_by_code(db, route.code)
    if existing:
        return None
    db_route = Route(
        code=route.code,
        departure_station_id=route.departure_station_id,
        arrival_station_id=route.arrival_station_id,
        distance_km=route.distance_km
    )
    db.add(db_route)
    db.commit()
    db.refresh(db_route)
    return db_route

def get_pricing_history(db: Session, route_id: int):
    return db.query(PricingHistory).filter(
        PricingHistory.route_id == route_id
    ).order_by(PricingHistory.effective_date.desc()).first()

def create_pricing(db: Session, pricing: PricingHistoryCreate):
    db_pricing = PricingHistory(
        route_id=pricing.route_id,
        price=pricing.price,
        effective_date=pricing.effective_date
    )
    db.add(db_pricing)
    db.commit()
    db.refresh(db_pricing)
    return db_pricing

def get_trip(db: Session, trip_id: int):
    return db.query(Trip).filter(Trip.id == trip_id).first()

def get_trips(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Trip).offset(skip).limit(limit).all()

def get_available_trips(db: Session, departure_station_id: int, arrival_station_id: int, date: datetime):
    return db.query(Trip).join(Route).filter(
        and_(
            Route.departure_station_id == departure_station_id,
            Route.arrival_station_id == arrival_station_id,
            Trip.departure_time >= date,
            Trip.is_active == True
        )
    ).all()


def _check_driver_conflict(
    db: Session,
    driver_id: int,
    departure_time,
    arrival_time=None,
    exclude_trip_id=None,
    buffer_minutes: int = 60,
) -> dict:
    """
    التحقق من عدم وجود تعارض للسائق/المساعد مع رحلات أخرى.
    
    القواعد:
    - الرحلات المتداخلة + فترة راحة (buffer_minutes) = تعارض
    - مثال: رحلة 1 من 10:00 → 14:00، buffer 60 دقيقة
    - يمكن قبول رحلة جديدة بعد 15:00 أو قبل 09:00
    
    Returns:
        {"has_conflict": bool, "conflict_trip_id": int, "conflict_range": str}
    """
    from datetime import timedelta

    if not driver_id:
        return {"has_conflict": False}

    # ✅ توحيد المنطقة الزمنية
    departure_time = _to_aware(departure_time)
    arrival_time = _to_aware(arrival_time)

    # حساب وقت الوصول الافتراضي (4 ساعات) إذا لم يُحدد
    if not arrival_time:
        arrival_time = departure_time + timedelta(hours=4)

    # نطاق الرحلة الجديدة (مع فترة الراحة)
    new_start = departure_time - timedelta(minutes=buffer_minutes)
    new_end = arrival_time + timedelta(minutes=buffer_minutes)

    # البحث عن رحلات نشطة لنفس السائق
    query = db.query(Trip).filter(
        Trip.is_active == True,
        (Trip.driver_id == driver_id) | (Trip.assistant_id == driver_id)
    )

    # استثناء الرحلة الحالية (عند التعديل)
    if exclude_trip_id:
        query = query.filter(Trip.id != exclude_trip_id)

    existing_trips = query.all()

    for existing in existing_trips:
        existing_start = _to_aware(existing.departure_time)
        existing_end = _to_aware(existing.arrival_time) or (existing_start + timedelta(hours=4))

        # فحص التداخل (مع buffer)
        # لا يوجد تداخل إذا: new_end <= existing_start  أو  new_start >= existing_end
        no_overlap = (new_end <= existing_start) or (new_start >= existing_end)

        if not no_overlap:
            return {
                "has_conflict": True,
                "conflict_trip_id": existing.id,
                "conflict_range": f"{existing_start.strftime('%Y-%m-%d %H:%M')} → {existing_end.strftime('%H:%M')}",
            }

    return {"has_conflict": False}


def _classify_employee_position(db: Session, position: str) -> str:
    """
    تصنيف وظيفة الموظف بالبحث في جدول positions.
    
    المنطق:
    1. نبحث عن الوظيفة بنفس الاسم (العربي) في جدول positions
    2. إذا وُجدت، نأخذ category منها (driver / assistant / admin / other)
    3. إذا لم تُوجد، نستخدم fallback نصي (للتوافق مع البيانات القديمة)
    """
    from app.models.positions_models import Position

    if not position:
        return "other"

    # 1) البحث في جدول positions بالاسم العربي
    pos = db.query(Position).filter(Position.name == position).first()
    if pos and pos.category:
        return pos.category

    # 2) البحث بالاسم الإنجليزي (احتياط)
    pos = db.query(Position).filter(Position.name_en == position).first()
    if pos and pos.category:
        return pos.category

    # 3) fallback نصي (للبيانات القديمة)
    p = position.strip().lower()
    if "مساعد" in p or "مضيف" in p or "host" in p or "assistant" in p:
        return "assistant"
    if "سائق" in p or "driver" in p:
        return "driver"

    return "other"


def get_available_drivers_for_trip(
    db: Session,
    departure_time,
    arrival_time=None,
    exclude_trip_id=None,
    buffer_minutes: int = 60,
):
    """
    جلب السائقين والمساعدين المتاحين لرحلة معينة.
    - يُفلتر حسب الوظيفة (سائق / مساعد سائق / مضيف)
    - يرجع 4 قوائم: متاحين ومشغولين لكل فئة
    """
    from app.models.employees_models import Employee

    employees = db.query(Employee).filter(Employee.is_active == True).all()

    available_drivers = []
    busy_drivers = []
    available_assistants = []
    busy_assistants = []

    for emp in employees:
        role = _classify_employee_position(db, emp.position)

        # تجاهل الموظفين الذين ليسوا سائقين ولا مساعدين
        if role == "other":
            continue

        conflict = _check_driver_conflict(
            db, emp.id, departure_time, arrival_time, exclude_trip_id, buffer_minutes
        )

        info = {
            "id": emp.id,
            "full_name": emp.full_name,
            "full_name_en": emp.full_name_en,
            "phone": emp.phone,
            "position": emp.position,
            "position_en": emp.position_en,
            "is_available": not conflict["has_conflict"],
            "conflict_trip_id": conflict.get("conflict_trip_id"),
            "conflict_range": conflict.get("conflict_range"),
        }

        if role == "driver":
            if conflict["has_conflict"]:
                busy_drivers.append(info)
            else:
                available_drivers.append(info)
        elif role == "assistant":
            if conflict["has_conflict"]:
                busy_assistants.append(info)
            else:
                available_assistants.append(info)

    return {
        "available_drivers": available_drivers,
        "busy_drivers": busy_drivers,
        "available_assistants": available_assistants,
        "busy_assistants": busy_assistants,
    }


def create_trip(db: Session, trip: TripCreate):
    # جلب أحدث سعر للمسار
    latest_price = get_pricing_history(db, trip.route_id)
    
    # جلب الحافلة للتحقق من وجودها
    bus = db.query(Bus).filter(Bus.id == trip.bus_id).first()
    if not bus:
        raise ValueError(f"الحافلة رقم {trip.bus_id} غير موجودة")
    
    # ========================================
    # ✅ التحقق من تعارض الحافلة مع رحلات أخرى
    # ========================================
    new_departure = _to_aware(trip.departure_time)
    new_arrival = _to_aware(trip.arrival_time) if trip.arrival_time else (new_departure + timedelta(hours=4))
    
    # جلب جميع الرحلات النشطة لنفس الحافلة
    existing_trips = db.query(Trip).filter(
        Trip.bus_id == trip.bus_id,
        Trip.is_active == True
    ).all()
    
    for existing in existing_trips:
        existing_dep = _to_aware(existing.departure_time)
        existing_arr = _to_aware(existing.arrival_time) if existing.arrival_time else (existing_dep + timedelta(hours=4))
        
        # فحص التداخل: هل الرحلتان تتقاطعان زمنياً؟
        # لا يوجد تداخل إذا: new_arrival <= existing_dep أو new_departure >= existing_arr
        if not (new_arrival <= existing_dep or new_departure >= existing_arr):
            raise ValueError(
                f"❌ تعارض: الحافلة مشغولة في رحلة أخرى "
                f"من {existing_dep.strftime('%Y-%m-%d %H:%M')} "
                f"حتى {existing_arr.strftime('%Y-%m-%d %H:%M')}"
            )
    
    # تعيين السعر
    if latest_price:
        price = latest_price.price
    else:
        price = trip.price_at_time or 0
        if price == 0:
            raise ValueError("لا يوجد سعر محدد لهذا المسار، يرجى إضافة سعر أولاً")
    
    db_trip = Trip(
        route_id=trip.route_id,
        bus_id=trip.bus_id,
        total_seats=bus.total_seats,
        departure_time=trip.departure_time,
        arrival_time=trip.arrival_time,
        price_at_time=price,
        is_active=trip.is_active,
        driver_id=trip.driver_id,
        assistant_id=trip.assistant_id,
    )
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    return db_trip


def update_trip_status(db: Session, trip_id: int, is_active: bool):
    trip = get_trip(db, trip_id)
    if trip:
        trip.is_active = is_active
        db.commit()
        db.refresh(trip)
    return trip

def update_trip(db: Session, trip_id: int, trip_data) -> Trip:
    """
    تحديث رحلة موجودة (بما فيها السائق والمساعد)
    
    القواعد:
    - لا يمكن التعديل بعد انطلاق الرحلة
    - التحقق من تعارض السائق/المساعد
    """
    from datetime import datetime

    db_trip = get_trip(db, trip_id)
    if not db_trip:
        return None

    # ✅ لا يمكن التعديل بعد الانطلاق
    from datetime import timezone
    now = datetime.now(timezone.utc)
    dep_time = _to_aware(db_trip.departure_time)
    if dep_time and dep_time < now:
        raise ValueError("❌ لا يمكن تعديل رحلة انطلقت بالفعل")

    # ✅ التحقق من توفر السائق (إن تغيّر)
    new_driver = getattr(trip_data, 'driver_id', None)
    if new_driver and new_driver != db_trip.driver_id:
        conflict = _check_driver_conflict(
            db, new_driver, db_trip.departure_time, db_trip.arrival_time,
            exclude_trip_id=trip_id
        )
        if conflict["has_conflict"]:
            raise ValueError(
                f"❌ السائق مشغول في رحلة أخرى: {conflict['conflict_range']}"
            )

    # ✅ التحقق من توفر المساعد (إن تغيّر)
    new_assistant = getattr(trip_data, 'assistant_id', None)
    if new_assistant and new_assistant != db_trip.assistant_id:
        conflict = _check_driver_conflict(
            db, new_assistant, db_trip.departure_time, db_trip.arrival_time,
            exclude_trip_id=trip_id
        )
        if conflict["has_conflict"]:
            raise ValueError(
                f"❌ المساعد مشغول في رحلة أخرى: {conflict['conflict_range']}"
            )

    # ✅ تحديث الحقول
    if hasattr(trip_data, 'driver_id'):
        db_trip.driver_id = trip_data.driver_id
    if hasattr(trip_data, 'assistant_id'):
        db_trip.assistant_id = trip_data.assistant_id
    if hasattr(trip_data, 'is_active'):
        db_trip.is_active = trip_data.is_active

    db.commit()
    db.refresh(db_trip)
    return db_trip


def get_last_crew_for_bus(db: Session, bus_id: int):
    """
    جلب آخر سائق ومساعد تم تعيينهما على هذا الباص.
    يُستخدم لتعيين السائق والمساعد تلقائيًا عند إنشاء رحلة جديدة.
    
    Returns:
        {"driver_id": int|None, "assistant_id": int|None}
    """
    # نبحث عن آخر رحلة لهذا الباص لها سائق أو مساعد
    last_trip = (
        db.query(Trip)
        .filter(
            Trip.bus_id == bus_id,
            (Trip.driver_id.isnot(None)) | (Trip.assistant_id.isnot(None))
        )
        .order_by(Trip.departure_time.desc())
        .first()
    )

    if not last_trip:
        return {"driver_id": None, "assistant_id": None}

    return {
        "driver_id": last_trip.driver_id,
        "assistant_id": last_trip.assistant_id,
    }


def get_live_trips(db: Session):
    """
    جلب الرحلات الحية (اليوم):
    - المغادرات (departures)
    - الوصولات (arrivals)
    
    مع معلومات:
    - المسار
    - السائق + المساعد
    - الباص
    - المقاعد المحجوزة والمتاحة
    - الحالة (departed / departing / upcoming)
    """
    from datetime import datetime, timezone, timedelta
    from app.models.bookings_models import Booking, BookingStatus, Passenger
    from app.models.employees_models import Employee
    from app.models.bus_models import Bus
    from app.models.stations_models import Station

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    # 
    # 1) المغادرات: الرحلات التي تنطلق اليوم
    # 
    departures_query = db.query(Trip).filter(
        Trip.is_active == True,
        Trip.departure_time >= today_start,
        Trip.departure_time < today_end,
    ).order_by(Trip.departure_time).all()

    # 
    # 2) الوصولات: الرحلات التي تصل اليوم
    # 
    arrivals_query = db.query(Trip).filter(
        Trip.is_active == True,
        Trip.arrival_time.isnot(None),
        Trip.arrival_time >= today_start,
        Trip.arrival_time < today_end,
    ).order_by(Trip.arrival_time).all()

    def enrich_trip(trip, ref_time):
        """إثراء بيانات الرحلة"""
        # المسار
        route = trip.route
        dep_station = route.departure_station if route else None
        arr_station = route.arrival_station if route else None

        # الباص
        bus = db.query(Bus).filter(Bus.id == trip.bus_id).first()

        # السائق والمساعد
        driver = None
        assistant = None
        if trip.driver_id:
            driver = db.query(Employee).filter(Employee.id == trip.driver_id).first()
        if trip.assistant_id:
            assistant = db.query(Employee).filter(Employee.id == trip.assistant_id).first()

        # عدد الحجوزات (غير ملغاة)
        bookings_count = db.query(Booking).filter(
            Booking.trip_id == trip.id,
            Booking.status != BookingStatus.CANCELLED,
        ).count()

        # المقاعد المحجوزة (العدد الفعلي)
        booked_seats = 0
        bookings = db.query(Booking).filter(
            Booking.trip_id == trip.id,
            Booking.status != BookingStatus.CANCELLED,
        ).all()
        for b in bookings:
            passenger = db.query(Passenger).filter(Passenger.id == b.passenger_id).first()
            if passenger and passenger.is_infant:
                continue
            booked_seats += len(b.seat_numbers or [])

        available_seats = trip.total_seats - booked_seats

        # حالة الرحلة
        dep_time = trip.departure_time
        if dep_time.tzinfo is None:
            dep_time = dep_time.replace(tzinfo=timezone.utc)

        diff = (dep_time - ref_time).total_seconds() / 60  # بالدقائق

        if diff < -15:
            status = "departed"          # انطلقت منذ أكثر من 15 دقيقة
        elif diff < 0:
            status = "just_departed"     # انطلقت قريبًا
        elif diff < 60:
            status = "departing_soon"    # تنطلق خلال ساعة
        elif diff < 180:
            status = "upcoming"          # تنطلق خلال 3 ساعات
        else:
            status = "later"             # لاحقًا

        # الوقت بصيغة ISO
        dep_iso = dep_time.isoformat() if dep_time else None
        arr_iso = None
        if trip.arrival_time:
            arr_t = trip.arrival_time
            if arr_t.tzinfo is None:
                arr_t = arr_t.replace(tzinfo=timezone.utc)
            arr_iso = arr_t.isoformat()

        #  التأكد من عدم وجود None (تستبدل بقيم افتراضية)
        return {
            "id": trip.id,
            "code": (route.code if route else "") or "",
            "departure_station": (dep_station.name if dep_station else "") or "",
            "departure_station_en": (dep_station.name_en if dep_station else "") or "",
            "arrival_station": (arr_station.name if arr_station else "") or "",
            "arrival_station_en": (arr_station.name_en if arr_station else "") or "",
            "departure_time": dep_iso or "",
            "arrival_time": arr_iso or "",
            "minutes_left": int(diff),
            "status": status,
            "bus": {
                "plate_number": (bus.plate_number if bus else "") or "",
                "model": (bus.model if bus else "") or "",
            } if bus else {"plate_number": "", "model": ""},
            "driver": {
                "id": driver.id,
                "name": driver.full_name or "",
                "name_en": driver.full_name_en or "",
                "phone": driver.phone or "",
            } if driver else None,
            "assistant": {
                "id": assistant.id,
                "name": assistant.full_name or "",
                "name_en": assistant.full_name_en or "",
            } if assistant else None,
            "bookings_count": bookings_count or 0,
            "booked_seats": booked_seats or 0,
            "available_seats": available_seats or 0,
            "total_seats": trip.total_seats or 0,
        }

    departures = [enrich_trip(t, now) for t in departures_query]
    arrivals = [enrich_trip(t, now) for t in arrivals_query]

    return {
        "now": now.isoformat(),
        "today": today_start.date().isoformat(),
        "departures": departures,
        "arrivals": arrivals,
        "departures_count": len(departures),
        "arrivals_count": len(arrivals),
    }
