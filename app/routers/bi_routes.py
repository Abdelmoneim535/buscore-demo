# -*- coding: utf-8 -*-
"""Router: BI Dashboard APIs"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from typing import Optional
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.database.database import get_db
from app.models.bookings_models import Booking, BookingStatus
from app.models.trips_models import Trip, Route
from app.models.customers_models import Customer
from app.models.branches_models import Branch
from app.models.bus_models import Bus
from app.models.employees_models import Employee
from app.models.expenses_models import Expense
from app.models.stations_models import City, Station

router = APIRouter(prefix="/bi", tags=["BI Dashboard"])


# 
# Helper: تحديد الفترة الزمنية
# 

def get_date_range(range_type: str, from_date: Optional[str] = None, to_date: Optional[str] = None):
    """إرجاع (start_date, end_date) حسب الفترة"""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if range_type == "today":
        return today_start, now
    elif range_type == "week":
        return today_start - timedelta(days=7), now
    elif range_type == "month":
        return today_start.replace(day=1), now
    elif range_type == "year":
        return today_start.replace(month=1, day=1), now
    elif range_type == "custom" and from_date and to_date:
        try:
            start = datetime.fromisoformat(from_date)
            end = datetime.fromisoformat(to_date)
            return start, end
        except:
            return today_start - timedelta(days=30), now
    else:
        # default: آخر 30 يوم
        return today_start - timedelta(days=30), now


# 
# Overview
# 



# ===========================================
# Helper: الفترة السابقة
# ===========================================
def get_previous_range(range_type: str, start, end):
    """يُرجع (prev_start, prev_end)"""
    from datetime import timedelta
    if range_type == "today":
        prev_start = start - timedelta(days=1)
        prev_end = end - timedelta(days=1)
    elif range_type == "week":
        prev_start = start - timedelta(days=7)
        prev_end = end - timedelta(days=7)
    elif range_type == "year":
        try:
            prev_start = start.replace(year=start.year - 1)
            prev_end = end.replace(year=end.year - 1)
        except ValueError:
            prev_start = start - timedelta(days=365)
            prev_end = end - timedelta(days=365)
    else:
        prev_end = start - timedelta(seconds=1)
        prev_start = (start - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return prev_start, prev_end


@router.get("/overview")
def get_overview(
    range_type: str = Query("month", description="today/week/month/year/custom"),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """نظرة عامة شاملة"""
    start_date, end_date = get_date_range(range_type, from_date, to_date)

    #  KPIs 

    # 1) إجمالي الإيرادات (من الحجوزات المؤكدة)
    total_revenue = db.query(func.coalesce(func.sum(Booking.total_price), 0)).filter(
        Booking.booked_at >= start_date,
        Booking.booked_at <= end_date,
        Booking.status != BookingStatus.CANCELLED,
    ).scalar() or 0

    # 2) عدد الحجوزات
    total_bookings = db.query(Booking).filter(
        Booking.booked_at >= start_date,
        Booking.booked_at <= end_date,
        Booking.status != BookingStatus.CANCELLED,
    ).count()

    # 3) عدد العملاء الفريدين
    total_customers = db.query(func.count(func.distinct(Booking.customer_id))).filter(
        Booking.booked_at >= start_date,
        Booking.booked_at <= end_date,
        Booking.customer_id.isnot(None),
    ).scalar() or 0

    # 4) عدد الرحلات
    total_trips = db.query(Trip).filter(
        Trip.departure_time >= start_date,
        Trip.departure_time <= end_date,
    ).count()

    # 5) الرحلات النشطة الآن
    active_trips = db.query(Trip).filter(
        Trip.departure_time <= datetime.now(timezone.utc),
        Trip.is_active == True,
    ).count()

    # 6) نسبة الإشغال
    trips_in_range = db.query(Trip).filter(
        Trip.departure_time >= start_date,
        Trip.departure_time <= end_date,
    ).all()

    total_seats = sum(t.total_seats for t in trips_in_range)
    booked_seats = 0
    for t in trips_in_range:
        booked = db.query(func.count(Booking.id)).filter(
            Booking.trip_id == t.id,
            Booking.status != BookingStatus.CANCELLED,
        ).scalar() or 0
        booked_seats += booked

    occupancy_rate = (booked_seats / total_seats * 100) if total_seats > 0 else 0

    #  الفروع 

    branches = db.query(Branch).filter(Branch.is_active == True).all()
    branches_data = []
    for b in branches:
        b_revenue = db.query(func.coalesce(func.sum(Booking.total_price), 0)).filter(
            Booking.branch_id == b.id,
            Booking.booked_at >= start_date,
            Booking.booked_at <= end_date,
            Booking.status != BookingStatus.CANCELLED,
        ).scalar() or 0

        b_bookings = db.query(Booking).filter(
            Booking.branch_id == b.id,
            Booking.booked_at >= start_date,
            Booking.booked_at <= end_date,
            Booking.status != BookingStatus.CANCELLED,
        ).count()

        branches_data.append({
            "id": b.id,
            "name": b.name,
            "name_en": b.name_en,
            "revenue": float(b_revenue),
            "bookings": b_bookings,
        })

    #  مصادر الحجوزات 

    sources_data = {}
    for source in ["office", "online", "app", "web"]:
        count = db.query(Booking).filter(
            Booking.booking_source == source,
            Booking.booked_at >= start_date,
            Booking.booked_at <= end_date,
            Booking.status != BookingStatus.CANCELLED,
        ).count()
        sources_data[source] = count

    #  الحجوزات الشهرية (آخر 6 أشهر) 

    monthly_bookings = []
    for i in range(5, -1, -1):
        month_start = (datetime.now(timezone.utc).replace(day=1) - timedelta(days=i * 30)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1)

        count = db.query(Booking).filter(
            Booking.booked_at >= month_start,
            Booking.booked_at < month_end,
            Booking.status != BookingStatus.CANCELLED,
        ).count()

        monthly_bookings.append({
            "month": month_start.strftime("%Y-%m"),
            "month_name": month_start.strftime("%B"),
            "count": count,
        })

    #  الإيرادات (30 يوم) 

    daily_revenue = []
    for i in range(29, -1, -1):
        day = (datetime.now(timezone.utc) - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day + timedelta(days=1)

        revenue = db.query(func.coalesce(func.sum(Booking.total_price), 0)).filter(
            Booking.booked_at >= day,
            Booking.booked_at < day_end,
            Booking.status != BookingStatus.CANCELLED,
        ).scalar() or 0

        daily_revenue.append({
            "date": day.strftime("%Y-%m-%d"),
            "revenue": float(revenue),
        })

    #  أفضل الرحلات 

    top_trips = db.query(
        Trip.id,
        Route.code,
        func.count(Booking.id).label("bookings_count"),
    ).join(
        Route, Route.id == Trip.route_id
    ).join(
        Booking, Booking.trip_id == Trip.id
    ).filter(
        Trip.departure_time >= start_date,
        Trip.departure_time <= end_date,
        Booking.status != BookingStatus.CANCELLED,
    ).group_by(Trip.id, Route.code).order_by(desc("bookings_count")).limit(5).all()

    top_trips_data = []
    for t in top_trips:
        route = db.query(Route).filter(Route.id == t.id).first()
        # أبسط: نستخدم الكود
        top_trips_data.append({
            "trip_id": t.id,
            "route_code": t.code,
            "bookings_count": t.bookings_count,
        })

    #  الجدول: آخر 5 حجوزات 

    recent_bookings = db.query(Booking).order_by(desc(Booking.booked_at)).limit(5).all()
    recent_data = []
    for r in recent_bookings:
        recent_data.append({
            "id": r.id,
            "reference": r.booking_reference,
            "pnr": r.pnr_reference,
            "total_price": float(r.total_price or 0),
            "status": str(r.status) if r.status else "",
            "booked_at": r.booked_at.isoformat() if r.booked_at else None,
        })

    return {
        "range": {
            "type": range_type,
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "kpis": {
            "total_revenue": float(total_revenue),
            "total_bookings": total_bookings,
            "total_customers": total_customers,
            "total_trips": total_trips,
            "active_trips": active_trips,
            "occupancy_rate": round(occupancy_rate, 1),
        },
        "branches": branches_data,
        "sources": sources_data,
        "monthly_bookings": monthly_bookings,
        "daily_revenue": daily_revenue,
        "top_trips": top_trips_data,
        "recent_bookings": recent_data,
    }


# 
# Luggage Analytics (إيراد الأمتعة)
# 
@router.get("/luggage")
async def get_luggage_analytics(
    range_type: str = "month",
    db: Session = Depends(get_db),
):
    """
    تحليل إيرادات الأمتعة:
    - إجمالي الإيراد
    - نسبة من الإيراد الكلي
    - توزيع حسب النوع
    - الإيراد الشهري
    - أعلى المسارات
    """
    from datetime import datetime, timedelta
    from sqlalchemy import func, and_

    # تحديد النطاق الزمني
    now = datetime.now()
    if range_type == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif range_type == "week":
        start_date = now - timedelta(days=7)
    elif range_type == "year":
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:  # month
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    try:
        from app.models.bookings_models import Luggage, BookingLuggage, Booking
        from app.models.trips_models import Trip, Route
        from app.models.stations_models import Station

        # إجمالي إيراد الأمتعة
        luggage_rev_q = (
            db.query(func.coalesce(func.sum(Luggage.price * BookingLuggage.quantity), 0))
            .join(BookingLuggage, BookingLuggage.luggage_id == Luggage.id)
            .join(Booking, Booking.id == BookingLuggage.booking_id)
            .filter(Booking.booked_at >= start_date)
        )
        luggage_revenue = float(luggage_rev_q.scalar() or 0)

        # إجمالي الإيرادات
        total_rev_q = db.query(func.coalesce(func.sum(Booking.total_price), 0)).filter(
            Booking.booked_at >= start_date
        )
        total_revenue = float(total_rev_q.scalar() or 0)

        # عدد الأمتعة
        count_q = (
            db.query(func.coalesce(func.sum(BookingLuggage.quantity), 0))
            .join(Booking, Booking.id == BookingLuggage.booking_id)
            .filter(Booking.booked_at >= start_date)
        )
        luggage_count = int(count_q.scalar() or 0)

        # متوسط الوزن
        avg_weight_q = db.query(func.coalesce(func.avg(Luggage.weight_kg), 0)).filter(
            Luggage.is_free == False
        )
        avg_weight = float(avg_weight_q.scalar() or 0)

        # توزيع حسب النوع
        by_type_q = (
            db.query(
                Luggage.luggage_type,
                func.count(BookingLuggage.booking_id).label("count"),
                func.coalesce(func.sum(Luggage.price * BookingLuggage.quantity), 0).label("revenue"),
            )
            .join(BookingLuggage, BookingLuggage.luggage_id == Luggage.id)
            .group_by(Luggage.luggage_type)
        )
        by_type = [
            {"type": row[0], "count": row[1], "revenue": float(row[2] or 0)}
            for row in by_type_q.all()
        ]

        # الإيراد الشهري (آخر 6 أشهر)
        monthly = []
        for i in range(5, -1, -1):
            month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = (month_start + timedelta(days=32)).replace(day=1)
            m_rev_q = (
                db.query(func.coalesce(func.sum(Luggage.price * BookingLuggage.quantity), 0))
                .join(BookingLuggage, BookingLuggage.luggage_id == Luggage.id)
                .join(Booking, Booking.id == BookingLuggage.booking_id)
                .filter(Booking.booked_at >= month_start, Booking.booked_at < next_month)
            )
            monthly.append({
                "month": month_start.strftime("%Y-%m"),
                "revenue": float(m_rev_q.scalar() or 0),
            })

        # أعلى المسارات
        top_routes_q = (
            db.query(
                Route.code,
                func.coalesce(func.sum(Luggage.price * BookingLuggage.quantity), 0).label("revenue"),
            )
            .select_from(Luggage)
            .join(BookingLuggage, BookingLuggage.luggage_id == Luggage.id)
            .join(Booking, Booking.id == BookingLuggage.booking_id)
            .join(Trip, Trip.id == Booking.trip_id)
            .join(Route, Route.id == Trip.route_id)
            .filter(Booking.booked_at >= start_date)
            .group_by(Route.code)
            .order_by(func.sum(Luggage.price * BookingLuggage.quantity).desc())
            .limit(5)
        )
        top_routes = [{"route": row[0], "revenue": float(row[1] or 0)} for row in top_routes_q.all()]

        # النسبة من الإجمالي
        percentage = round((luggage_revenue / total_revenue * 100) if total_revenue > 0 else 0, 1)

        return {
            "kpis": {
                "luggage_revenue": luggage_revenue,
                "percentage": percentage,
                "luggage_count": luggage_count,
                "avg_weight": round(avg_weight, 1),
            },
            "monthly": monthly,
            "by_type": by_type,
            "top_routes": top_routes,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "kpis": {}, "monthly": [], "by_type": [], "top_routes": []}


# 
# Occupancy Analytics (نسبة الإشغال / Manifest)
# 
@router.get("/occupancy")
async def get_occupancy_analytics(
    range_type: str = "month",
    db: Session = Depends(get_db),
):
    """
    تحليل نسبة الإشغال:
    - متوسط الإشغال
    - التذاكر المُباعة
    - المقاعد الشاغرة
    - الإشغال حسب الخط
    - المسارات ذات المقاعد الشاغرة
    """
    from datetime import datetime, timedelta
    from sqlalchemy import func

    now = datetime.now()
    if range_type == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif range_type == "week":
        start_date = now - timedelta(days=7)
    elif range_type == "year":
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    try:
        from app.models.bookings_models import Booking
        from app.models.trips_models import Trip, Route

        # كل الرحلات في النطاق
        trips_q = db.query(Trip).filter(Trip.departure_time >= start_date, Trip.is_active == True).all()

        total_seats = 0
        sold_seats = 0
        by_route = {}

        for trip in trips_q:
            trip_seats = trip.total_seats or 0
            total_seats += trip_seats

            # عدد الحجوزات في هذه الرحلة (بدون الملغاة)
            booked = (
                db.query(func.count(Booking.id))
                .filter(Booking.trip_id == trip.id, Booking.status != "CANCELLED")
                .scalar()
                or 0
            )
            sold_seats += booked

            # تجميع حسب الخط
            route = db.query(Route).filter(Route.id == trip.route_id).first()
            route_code = route.code if route else f"Route-{trip.route_id}"
            if route_code not in by_route:
                by_route[route_code] = {"sold": 0, "total": 0}
            by_route[route_code]["sold"] += booked
            by_route[route_code]["total"] += trip_seats

        empty_seats = total_seats - sold_seats
        avg_occupancy = round((sold_seats / total_seats * 100) if total_seats > 0 else 0, 1)

        # أعلى إشغال
        top_route = None
        top_pct = 0
        for code, data in by_route.items():
            pct = (data["sold"] / data["total"] * 100) if data["total"] > 0 else 0
            if pct > top_pct:
                top_pct = pct
                top_route = code

        # الإشغال حسب الخط
        by_route_list = []
        low_occupancy = []
        for code, data in by_route.items():
            pct = round((data["sold"] / data["total"] * 100) if data["total"] > 0 else 0, 1)
            item = {
                "route": code,
                "sold": data["sold"],
                "total": data["total"],
                "empty": data["total"] - data["sold"],
                "occupancy": pct,
            }
            by_route_list.append(item)
            if pct < 60:
                low_occupancy.append(item)

        by_route_list.sort(key=lambda x: x["occupancy"], reverse=True)
        low_occupancy.sort(key=lambda x: x["occupancy"])

        return {
            "kpis": {
                "avg_occupancy": avg_occupancy,
                "sold_tickets": sold_seats,
                "empty_seats": empty_seats,
                "top_route": top_route or "",
            },
            "by_route": by_route_list,
            "low_occupancy_routes": low_occupancy,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "kpis": {}, "by_route": [], "low_occupancy_routes": []}


# 
# RFM Analysis (تصنيف العملاء)
# 
@router.get("/rfm")
async def get_rfm_analytics(
    range_type: str = "month",
    db: Session = Depends(get_db),
):
    """
    تحليل RFM:
    - R (Recency): آخر حجز
    - F (Frequency): عدد الحجوزات
    - M (Monetary): إجمالي الإنفاق
    
    التصنيفات: VIP / دائم / جديد / خامل
    """
    from datetime import datetime, timedelta

    now = datetime.now()
    try:
        from app.models.customers_models import Customer

        # جميع العملاء النشطين
        customers = db.query(Customer).filter(Customer.is_active == True).all()

        if not customers:
            return {
                "kpis": {"total": 0, "vip": 0, "regular": 0, "new": 0, "dormant": 0},
                "distribution": [],
                "top_customers": [],
                "monthly_growth": [],
            }

        # حساب RFM لكل عميل
        customers_rfm = []
        for c in customers:
            # R: عدد الأيام منذ آخر حجز
            if c.last_booking_at:
                days_since = (now - c.last_booking_at).days
            else:
                days_since = 9999

            # F: عدد الحجوزات
            freq = c.total_bookings or 0

            # M: إجمالي الإنفاق
            monetary = float(c.total_spent or 0)

            customers_rfm.append({
                "id": c.id,
                "name": c.full_name,
                "phone": c.phone,
                "is_vip": bool(c.is_vip),
                "recency_days": days_since,
                "frequency": freq,
                "monetary": monetary,
                "created_at": c.created_at,
                "last_booking_at": c.last_booking_at,
            })

        # تصنيف العملاء
        # VIP: F >= 5 أو M >= 100K، R < 30 يوم
        # دائم: F >= 3 أو M >= 50K، R < 60 يوم
        # جديد: F < 3، R < 60 يوم
        # خامل: R >= 60 يوم

        vip_list = []
        regular_list = []
        new_list = []
        dormant_list = []

        for c in customers_rfm:
            is_vip_flag = c["is_vip"]
            r = c["recency_days"]
            f = c["frequency"]
            m = c["monetary"]

            if is_vip_flag or (r < 30 and (f >= 5 or m >= 100000)):
                vip_list.append(c)
            elif r < 60 and (f >= 3 or m >= 50000):
                regular_list.append(c)
            elif r < 60:
                new_list.append(c)
            else:
                dormant_list.append(c)

        # أفضل 10 عملاء VIP
        top_customers = sorted(
            vip_list + regular_list,
            key=lambda x: (x["monetary"], x["frequency"]),
            reverse=True,
        )[:10]

        # نمو شهري (آخر 6 أشهر)
        monthly_growth = []
        for i in range(5, -1, -1):
            month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = (month_start + timedelta(days=32)).replace(day=1)

            count = (
                db.query(Customer)
                .filter(
                    Customer.created_at >= month_start,
                    Customer.created_at < next_month,
                    Customer.is_active == True,
                )
                .count()
            )
            monthly_growth.append({
                "month": month_start.strftime("%Y-%m"),
                "count": count,
            })

        return {
            "kpis": {
                "total": len(customers_rfm),
                "vip": len(vip_list),
                "regular": len(regular_list),
                "new": len(new_list),
                "dormant": len(dormant_list),
            },
            "distribution": [
                {"type": "VIP", "count": len(vip_list), "color": "#ffc107"},
                {"type": "دائم", "count": len(regular_list), "color": "#198754"},
                {"type": "جديد", "count": len(new_list), "color": "#0d6efd"},
                {"type": "خامل", "count": len(dormant_list), "color": "#6c757d"},
            ],
            "top_customers": top_customers,
            "monthly_growth": monthly_growth,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "kpis": {}, "distribution": [], "top_customers": [], "monthly_growth": []}


# ===========================================
# Branches Analytics
# ===========================================
@router.get("/branches")
def get_branches_analytics(
    range_type: str = Query("month"),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    compare_with: str = Query(""),
    db: Session = Depends(get_db),
):
    """تحليل الفروع"""
    start_date, end_date = get_date_range(range_type, from_date, to_date)

    try:
        branches = db.query(Branch).filter(Branch.is_active == True).all()
        branches_list = []
        total_revenue = 0
        total_bookings = 0
        total_employees = 0

        for b in branches:
            b_revenue = db.query(func.coalesce(func.sum(Booking.total_price), 0)).filter(
                Booking.branch_id == b.id,
                Booking.booked_at >= start_date,
                Booking.booked_at <= end_date,
                Booking.status != BookingStatus.CANCELLED,
            ).scalar() or 0

            b_bookings = db.query(Booking).filter(
                Booking.branch_id == b.id,
                Booking.booked_at >= start_date,
                Booking.booked_at <= end_date,
                Booking.status != BookingStatus.CANCELLED,
            ).count()

            b_employees = db.query(Employee).filter(
                Employee.branch_id == b.id,
                Employee.is_active == True,
            ).count()

            city_name = ""
            if b.city_id:
                city = db.query(City).filter(City.id == b.city_id).first()
                if city:
                    city_name = city.name

            total_revenue += float(b_revenue)
            total_bookings += b_bookings
            total_employees += b_employees

            branches_list.append({
                "id": b.id,
                "name": b.name,
                "name_en": b.name_en,
                "code": b.code,
                "city": city_name,
                "revenue": float(b_revenue),
                "bookings": b_bookings,
                "employees": b_employees,
                "is_active": bool(b.is_active),
            })

        branches_list.sort(key=lambda x: x["revenue"], reverse=True)
        top_branch = branches_list[0]["name"] if branches_list else ""
        bottom_branch = branches_list[-1]["name"] if len(branches_list) > 1 else ""
        avg_revenue = (total_revenue / len(branches_list)) if branches_list else 0

        monthly = []
        now = datetime.now()
        for i in range(5, -1, -1):
            month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = (month_start + timedelta(days=32)).replace(day=1)
            m_rev = db.query(func.coalesce(func.sum(Booking.total_price), 0)).filter(
                Booking.booked_at >= month_start,
                Booking.booked_at < next_month,
                Booking.status != BookingStatus.CANCELLED,
            ).scalar() or 0
            monthly.append({"month": month_start.strftime("%Y-%m"), "revenue": float(m_rev)})

        comparison = {}
        if compare_with in ("prev_month", "prev_year"):
            prev_start, prev_end = get_previous_range(range_type, start_date, end_date)
            prev_rev = db.query(func.coalesce(func.sum(Booking.total_price), 0)).filter(
                Booking.booked_at >= prev_start,
                Booking.booked_at < prev_end,
                Booking.status != BookingStatus.CANCELLED,
            ).scalar() or 0
            prev_bookings = db.query(Booking).filter(
                Booking.booked_at >= prev_start,
                Booking.booked_at < prev_end,
                Booking.status != BookingStatus.CANCELLED,
            ).count()

            def _change(cur, prev):
                if prev == 0:
                    return 100.0 if cur > 0 else 0.0
                return round(((cur - prev) / prev) * 100, 1)

            comparison = {
                "revenue_change": _change(total_revenue, float(prev_rev)),
                "bookings_change": _change(total_bookings, prev_bookings),
            }

        return {
            "kpis": {
                "total": len(branches_list),
                "top_branch": top_branch,
                "bottom_branch": bottom_branch,
                "avg_revenue": avg_revenue,
                "total_employees": total_employees,
                "total_revenue": total_revenue,
                "total_bookings": total_bookings,
            },
            "comparison": comparison,
            "list": branches_list,
            "monthly": monthly,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "kpis": {}, "list": [], "monthly": []}


# 
# Cities Analytics
# 
@router.get("/cities")
def get_cities_analytics(
    range_type: str = Query("month"),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    compare_with: str = Query(""),
    db: Session = Depends(get_db),
):
    """تحليل المدن"""
    start_date, end_date = get_date_range(range_type, from_date, to_date)

    try:
        cities = db.query(City).all()
        cities_list = []
        total_bookings = 0
        total_revenue = 0

        for c in cities:
            # الإيرادات  من الرحلات التي تبدأ في هذه المدينة (departure) لتجنب التكرار
            revenue_q = (
                db.query(func.coalesce(func.sum(Booking.total_price), 0))
                .join(Trip, Trip.id == Booking.trip_id)
                .join(Route, Route.id == Trip.route_id)
                .join(Station, Route.departure_station_id == Station.id)
                .filter(
                    Station.city_id == c.id,
                    Booking.booked_at >= start_date,
                    Booking.booked_at <= end_date,
                    Booking.status != BookingStatus.CANCELLED,
                )
            )
            c_revenue = revenue_q.scalar() or 0

            # عدد الحجوزات  نفس المنطق
            bookings_q = (
                db.query(Booking)
                .join(Trip, Trip.id == Booking.trip_id)
                .join(Route, Route.id == Trip.route_id)
                .join(Station, Route.departure_station_id == Station.id)
                .filter(
                    Station.city_id == c.id,
                    Booking.booked_at >= start_date,
                    Booking.booked_at <= end_date,
                    Booking.status != BookingStatus.CANCELLED,
                )
            )
            c_bookings = bookings_q.count()

            total_revenue += float(c_revenue)
            total_bookings += c_bookings

            # النمو (تبسيط  0 للتجربة)
            growth = 0

            cities_list.append({
                "id": c.id,
                "name": c.name,
                "name_en": c.name_en,
                "code": c.code,
                "revenue": float(c_revenue),
                "bookings": c_bookings,
                "growth": growth,
            })

        cities_list.sort(key=lambda x: x["revenue"], reverse=True)

        # الأكثر والأقل حجزا
        top_city = cities_list[0]["name"] if cities_list else ""
        bottom_city = cities_list[-1]["name"] if len(cities_list) > 1 else ""
        avg_revenue = (total_revenue / len(cities_list)) if cities_list else 0
        total_trips = db.query(Trip).filter(
            Trip.departure_time >= start_date,
            Trip.departure_time <= end_date,
        ).count()

        # النمو الشهري
        monthly = []
        now = datetime.now()
        for i in range(5, -1, -1):
            month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = (month_start + timedelta(days=32)).replace(day=1)
            m_count = db.query(Booking).filter(
                Booking.booked_at >= month_start,
                Booking.booked_at < next_month,
                Booking.status != BookingStatus.CANCELLED,
            ).count()
            monthly.append({"month": month_start.strftime("%Y-%m"), "count": m_count})

        # المقارنة
        comparison = {}
        if compare_with in ("prev_month", "prev_year"):
            prev_start, prev_end = get_previous_range(range_type, start_date, end_date)
            prev_rev = db.query(func.coalesce(func.sum(Booking.total_price), 0)).filter(
                Booking.booked_at >= prev_start,
                Booking.booked_at < prev_end,
                Booking.status != BookingStatus.CANCELLED,
            ).scalar() or 0
            prev_bookings = db.query(Booking).filter(
                Booking.booked_at >= prev_start,
                Booking.booked_at < prev_end,
                Booking.status != BookingStatus.CANCELLED,
            ).count()

            def _change(cur, prev):
                if prev == 0:
                    return 100.0 if cur > 0 else 0.0
                return round(((cur - prev) / prev) * 100, 1)

            comparison = {
                "revenue_change": _change(total_revenue, float(prev_rev)),
                "bookings_change": _change(total_bookings, prev_bookings),
            }

        # النمو الأعلى (تبسيط  أعلى مدينة)
        top_growth = cities_list[0]["name"] if cities_list else ""

        return {
            "kpis": {
                "total": len(cities_list),
                "top_city": top_city,
                "bottom_city": bottom_city,
                "total_trips": total_trips,
                "avg_revenue": avg_revenue,
                "top_growth": top_growth,
                "total_bookings": total_bookings,
                "total_revenue": total_revenue,
            },
            "comparison": comparison,
            "list": cities_list,
            "monthly": monthly,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "kpis": {}, "list": [], "monthly": []}


# 
# Buses Analytics
# 
@router.get("/buses")
def get_buses_analytics(
    range_type: str = Query("month"),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    compare_with: str = Query(""),
    db: Session = Depends(get_db),
):
    """تحليل الحافلات"""
    start_date, end_date = get_date_range(range_type, from_date, to_date)

    try:
        buses = db.query(Bus).all()
        total = len(buses)
        active = sum(1 for b in buses if b.is_active)
        inactive = total - active
        utilization = int(round((active / total * 100) if total > 0 else 0))
        maintenance = 0

        types_dict = {}
        for b in buses:
            model = b.model or "غير محدد"
            types_dict[model] = types_dict.get(model, 0) + 1
        types_list = [{"name": k, "count": v} for k, v in types_dict.items()]

        top_by_revenue = []
        for b in buses:
            b_revenue = (
                db.query(func.coalesce(func.sum(Booking.total_price), 0))
                .join(Trip, Trip.id == Booking.trip_id)
                .filter(
                    Trip.bus_id == b.id,
                    Booking.booked_at >= start_date,
                    Booking.booked_at <= end_date,
                    Booking.status != BookingStatus.CANCELLED,
                )
                .scalar() or 0
            )
            b_trips = db.query(Trip).filter(
                Trip.bus_id == b.id,
                Trip.departure_time >= start_date,
                Trip.departure_time <= end_date,
            ).count()
            b_bookings = (
                db.query(Booking)
                .join(Trip, Trip.id == Booking.trip_id)
                .filter(
                    Trip.bus_id == b.id,
                    Booking.booked_at >= start_date,
                    Booking.booked_at <= end_date,
                    Booking.status != BookingStatus.CANCELLED,
                )
                .count()
            )
            efficiency = min(100, int(float(b_revenue) / 1000000 * 100)) if b_revenue > 0 else 0

            top_by_revenue.append({
                "id": b.id,
                "plate": b.plate_number,
                "model": b.model,
                "year": b.year,
                "total_seats": b.total_seats,
                "revenue": float(b_revenue),
                "trips": b_trips,
                "bookings": b_bookings,
                "efficiency": efficiency,
                "is_active": bool(b.is_active),
            })

        top_by_revenue.sort(key=lambda x: x["revenue"], reverse=True)
        top_by_revenue = top_by_revenue[:10]

        monthly_maintenance = []
        now = datetime.now()
        for i in range(5, -1, -1):
            month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = (month_start + timedelta(days=32)).replace(day=1)
            m_trips = db.query(Trip).filter(
                Trip.departure_time >= month_start,
                Trip.departure_time < next_month,
            ).count()
            monthly_maintenance.append({
                "month": month_start.strftime("%Y-%m"),
                "count": m_trips,
            })

        comparison = {}
        if compare_with in ("prev_month", "prev_year"):
            prev_start, prev_end = get_previous_range(range_type, start_date, end_date)
            prev_rev = (
                db.query(func.coalesce(func.sum(Booking.total_price), 0))
                .join(Trip, Trip.id == Booking.trip_id)
                .filter(
                    Booking.booked_at >= prev_start,
                    Booking.booked_at < prev_end,
                    Booking.status != BookingStatus.CANCELLED,
                )
                .scalar() or 0
            )
            total_rev = sum(b["revenue"] for b in top_by_revenue)

            def _change(cur, prev):
                if prev == 0:
                    return 100.0 if cur > 0 else 0.0
                return round(((cur - prev) / prev) * 100, 1)

            comparison = {"revenue_change": _change(total_rev, float(prev_rev))}

        return {
            "kpis": {
                "total": total,
                "active": active,
                "inactive": inactive,
                "maintenance": maintenance,
                "utilization": utilization,
            },
            "comparison": comparison,
            "types": types_list,
            "top_by_revenue": top_by_revenue,
            "monthly_maintenance": monthly_maintenance,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "kpis": {}, "types": [], "top_by_revenue": [], "monthly_maintenance": []}


# 
# Employees Analytics
# 
@router.get("/employees")
def get_employees_analytics(
    range_type: str = Query("month"),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    compare_with: str = Query(""),
    db: Session = Depends(get_db),
):
    """تحليل الموظفين"""
    try:
        employees = db.query(Employee).all()
        total = len(employees)
        active = sum(1 for e in employees if e.is_active)

        total_salary = sum(float(e.base_salary or 0) for e in employees if e.is_active)
        avg_salary = (total_salary / active) if active > 0 else 0

        # أعلى راتبا
        top_salary_emp = max(employees, key=lambda e: float(e.base_salary or 0)) if employees else None
        top_salary_name = top_salary_emp.full_name if top_salary_emp else ""

        # توزيع حسب المنصب
        positions_dict = {}
        for e in employees:
            pos = e.position or "غير محدد"
            if pos not in positions_dict:
                positions_dict[pos] = {"count": 0, "salary": 0}
            positions_dict[pos]["count"] += 1
            positions_dict[pos]["salary"] += float(e.base_salary or 0)

        positions_list = [
            {"name": k, "count": v["count"], "salary": v["salary"]}
            for k, v in positions_dict.items()
        ]

        # قائمة الموظفين
        employees_list = []
        for e in employees:
            branch_name = ""
            if e.branch_id:
                branch = db.query(Branch).filter(Branch.id == e.branch_id).first()
                if branch:
                    branch_name = branch.name

            employees_list.append({
                "id": e.id,
                "name": e.full_name,
                "name_en": e.full_name_en,
                "position": e.position,
                "position_en": e.position_en,
                "phone": e.phone,
                "salary": float(e.base_salary or 0),
                "hire_date": e.hire_date.isoformat() if e.hire_date else None,
                "branch": branch_name,
                "is_active": bool(e.is_active),
            })

        employees_list.sort(key=lambda x: x["salary"], reverse=True)

        return {
            "kpis": {
                "total": total,
                "active": active,
                "total_salary": total_salary,
                "avg_salary": avg_salary,
                "top_salary_name": top_salary_name,
                "top_salary": float(top_salary_emp.base_salary or 0) if top_salary_emp else 0,
            },
            "comparison": {},
            "positions": positions_list,
            "list": employees_list,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "kpis": {}, "positions": [], "list": []}


# 
# Financial Analytics
# 
@router.get("/financial")
def get_financial_analytics(
    range_type: str = Query("month"),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    compare_with: str = Query(""),
    db: Session = Depends(get_db),
):
    """تحليل المالية"""
    start_date, end_date = get_date_range(range_type, from_date, to_date)

    try:
        # الإيرادات من الحجوزات
        total_revenue = db.query(func.coalesce(func.sum(Booking.total_price), 0)).filter(
            Booking.booked_at >= start_date,
            Booking.booked_at <= end_date,
            Booking.status != BookingStatus.CANCELLED,
        ).scalar() or 0

        # المصروفات  من جدول expenses
        try:
            from app.models.expenses_models import Expense as ExpModel, ExpenseCategory
        except:
            ExpModel = None
            ExpenseCategory = None

        total_expenses = 0
        expense_categories = []

        if ExpModel:
            total_expenses = db.query(func.coalesce(func.sum(ExpModel.amount), 0)).filter(
                ExpModel.expense_date >= start_date,
                ExpModel.expense_date <= end_date,
            ).scalar() or 0

            # حسب الفئة
            if ExpenseCategory:
                cats = db.query(ExpenseCategory).all()
                for cat in cats:
                    amount = db.query(func.coalesce(func.sum(ExpModel.amount), 0)).filter(
                        ExpModel.category_id == cat.id,
                        ExpModel.expense_date >= start_date,
                        ExpModel.expense_date <= end_date,
                    ).scalar() or 0
                    if amount > 0:
                        expense_categories.append({
                            "name": cat.name,
                            "name_en": cat.name_en,
                            "amount": float(amount),
                        })

        total_revenue = float(total_revenue)
        total_expenses = float(total_expenses)
        profit = total_revenue - total_expenses
        margin = round((profit / total_revenue * 100), 1) if total_revenue > 0 else 0

        # أعلى فئة
        top_category = expense_categories[0]["name"] if expense_categories else ""
        if expense_categories:
            expense_categories.sort(key=lambda x: x["amount"], reverse=True)
            top_category = expense_categories[0]["name"]

        # الشهري  إيرادات ومصروفات (آخر 6 أشهر)
        monthly = []
        now = datetime.now()
        for i in range(5, -1, -1):
            month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = (month_start + timedelta(days=32)).replace(day=1)

            m_rev = db.query(func.coalesce(func.sum(Booking.total_price), 0)).filter(
                Booking.booked_at >= month_start,
                Booking.booked_at < next_month,
                Booking.status != BookingStatus.CANCELLED,
            ).scalar() or 0

            m_exp = 0
            if ExpModel:
                m_exp = db.query(func.coalesce(func.sum(ExpModel.amount), 0)).filter(
                    ExpModel.expense_date >= month_start,
                    ExpModel.expense_date < next_month,
                ).scalar() or 0

            monthly.append({
                "month": month_start.strftime("%Y-%m"),
                "revenue": float(m_rev),
                "expenses": float(m_exp),
                "profit": float(m_rev) - float(m_exp),
            })

        return {
            "kpis": {
                "revenue": total_revenue,
                "expenses": total_expenses,
                "profit": profit,
                "margin": margin,
                "top_category": top_category,
            },
            "comparison": {},
            "expense_categories": expense_categories,
            "monthly": monthly,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "kpis": {}, "expense_categories": [], "monthly": []}


# 
# Heat Map  أوقات الذروة × أيام الأسبوع
# 
@router.get("/heatmap")
def get_heatmap_analytics(
    range_type: str = Query("month"),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """تحليل أوقات الذروة"""
    start_date, end_date = get_date_range(range_type, from_date, to_date)

    try:
        days_ar = ["الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]
        hours = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

        # نُنشئ مصفوفة 7×15
        matrix = [[0] * len(hours) for _ in range(7)]

        # كل الحجوزات في النطاق
        bookings = db.query(Booking).filter(
            Booking.booked_at >= start_date,
            Booking.booked_at <= end_date,
            Booking.status != BookingStatus.CANCELLED,
        ).all()

        # نوزّع حسب اليوم والساعة
        for b in bookings:
            if not b.booked_at:
                continue
            day_idx = (b.booked_at.weekday() + 1) % 7  # 0=Sunday
            hour = b.booked_at.hour
            if hour in hours:
                hour_idx = hours.index(hour)
                matrix[day_idx][hour_idx] += 1

        # نجد أعلى قيمة
        max_val = max(max(row) for row in matrix) if any(any(row) for row in matrix) else 0

        # Peak time
        peak_day = ""
        peak_hour = ""
        peak_count = 0
        for d in range(7):
            for h in range(len(hours)):
                if matrix[d][h] > peak_count:
                    peak_count = matrix[d][h]
                    peak_day = days_ar[d]
                    peak_hour = f"{hours[h]:02d}:00"

        total_bookings = sum(sum(row) for row in matrix)

        return {
            "kpis": {
                "total": total_bookings,
                "peak_day": peak_day,
                "peak_hour": peak_hour,
                "peak_count": peak_count,
                "max_value": max_val,
            },
            "days": days_ar,
            "hours": [f"{h:02d}:00" for h in hours],
            "matrix": matrix,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "kpis": {}, "days": [], "hours": [], "matrix": []}


# 
# ABC Analysis  تصنيف الحافلات حسب الإيراد
# 
@router.get("/abc-analysis")
def get_abc_analysis(
    range_type: str = Query("month"),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """ABC Analysis للحافلات"""
    start_date, end_date = get_date_range(range_type, from_date, to_date)

    try:
        buses = db.query(Bus).all()
        buses_data = []

        for b in buses:
            b_revenue = (
                db.query(func.coalesce(func.sum(Booking.total_price), 0))
                .join(Trip, Trip.id == Booking.trip_id)
                .filter(
                    Trip.bus_id == b.id,
                    Booking.booked_at >= start_date,
                    Booking.booked_at <= end_date,
                    Booking.status != BookingStatus.CANCELLED,
                )
                .scalar() or 0
            )

            b_trips = db.query(Trip).filter(
                Trip.bus_id == b.id,
                Trip.departure_time >= start_date,
                Trip.departure_time <= end_date,
            ).count()

            b_bookings = (
                db.query(Booking)
                .join(Trip, Trip.id == Booking.trip_id)
                .filter(
                    Trip.bus_id == b.id,
                    Booking.booked_at >= start_date,
                    Booking.booked_at <= end_date,
                    Booking.status != BookingStatus.CANCELLED,
                )
                .count()
            )

            buses_data.append({
                "id": b.id,
                "plate": b.plate_number,
                "model": b.model,
                "year": b.year,
                "revenue": float(b_revenue),
                "trips": b_trips,
                "bookings": b_bookings,
            })

        # ترتيب تنازلي حسب الإيراد
        buses_data.sort(key=lambda x: x["revenue"], reverse=True)

        total_revenue = sum(b["revenue"] for b in buses_data)
        cumulative = 0
        total_buses = len(buses_data)
        a_cutoff = max(1, int(total_buses * 0.2))
        b_cutoff = max(a_cutoff + 1, int(total_buses * 0.5))

        # تصنيف ABC
        for b in buses_data:
            if total_revenue > 0:
                b["percentage"] = round((b["revenue"] / total_revenue) * 100, 1)
            else:
                b["percentage"] = 0.0

            prev_cumulative = cumulative
            cumulative += b["percentage"]
            b["cumulative"] = round(cumulative, 1)

            # التصنيف حسب الوضع قبل الإضافة
            # A: 0-80%  B: 80-95%  C: 95-100%
            if prev_cumulative < 80:
                b["class"] = "A"
            elif prev_cumulative < 95:
                b["class"] = "B"
            else:
                b["class"] = "C"

        # إحصائيات
        a_count = sum(1 for b in buses_data if b["class"] == "A")
        b_count = sum(1 for b in buses_data if b["class"] == "B")
        c_count = sum(1 for b in buses_data if b["class"] == "C")

        a_revenue = sum(b["revenue"] for b in buses_data if b["class"] == "A")
        b_revenue = sum(b["revenue"] for b in buses_data if b["class"] == "B")
        c_revenue = sum(b["revenue"] for b in buses_data if b["class"] == "C")

        total = len(buses_data)

        return {
            "kpis": {
                "total_buses": total,
                "total_revenue": total_revenue,
                "class_a_count": a_count,
                "class_b_count": b_count,
                "class_c_count": c_count,
                "class_a_revenue": a_revenue,
                "class_b_revenue": b_revenue,
                "class_c_revenue": c_revenue,
                "class_a_percentage": round((a_revenue / total_revenue) * 100, 1) if total_revenue > 0 else 0,
                "class_b_percentage": round((b_revenue / total_revenue) * 100, 1) if total_revenue > 0 else 0,
                "class_c_percentage": round((c_revenue / total_revenue) * 100, 1) if total_revenue > 0 else 0,
            },
            "list": buses_data,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "kpis": {}, "list": []}
