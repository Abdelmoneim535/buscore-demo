from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database.database import get_db
from app.routers.auth_routes import get_current_admin
from app.crud import trips_crud
from app.crud import stations_crud
from app.schemas.trips_schemas import (
    RouteCreate, RouteResponse,
    PricingHistoryCreate, PricingHistoryResponse,
    TripCreate, TripResponse,
    DriverAvailabilityResponse,
)

router = APIRouter(prefix="/trips", tags=["المسارات والرحلات"])

@router.get("/bus/{bus_id}/last-crew", dependencies=[Depends(get_current_admin)])
def get_bus_last_crew(bus_id: int, db: Session = Depends(get_db)):
    """
    جلب آخر سائق ومساعد تم تعيينهما على هذا الباص
    """
    return trips_crud.get_last_crew_for_bus(db, bus_id)


@router.get("/available-drivers", response_model=DriverAvailabilityResponse, dependencies=[Depends(get_current_admin)])
def get_available_drivers(
    departure_time: datetime = Query(...),
    arrival_time: datetime = Query(None),
    exclude_trip_id: int = Query(None),
    buffer_minutes: int = Query(60),
    db: Session = Depends(get_db),
):
    """
    جلب السائقين/الموظفين مع حالة توفرهم في وقت الرحلة.
    - available: متاحون
    - busy: مشغولون (مع بيان الرحلة المتعارضة)
    """
    return trips_crud.get_available_drivers_for_trip(
        db,
        departure_time=departure_time,
        arrival_time=arrival_time,
        exclude_trip_id=exclude_trip_id,
        buffer_minutes=buffer_minutes,
    )


@router.get("/live")
def get_live_trips_endpoint(db: Session = Depends(get_db)):
    """
    الرحلات الحية (اليوم):
    - المغادرات
    - الوصولات
    """
    return trips_crud.get_live_trips(db)


@router.get("/routes", response_model=List[RouteResponse])
def get_routes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return trips_crud.get_routes(db, skip=skip, limit=limit)

@router.post("/routes", response_model=RouteResponse, dependencies=[Depends(get_current_admin)])
def create_route(route: RouteCreate, db: Session = Depends(get_db)):
    # التحقق من عدم وجود مسار بنفس الكود
    existing = trips_crud.get_route_by_code(db, route.code)
    if existing:
        raise HTTPException(status_code=400, detail=f"المسار بالكود {route.code} موجود مسبقاً")
    
    # ✅ التحقق من وجود محطة المغادرة
    departure_station = stations_crud.get_station(db, route.departure_station_id)
    if not departure_station:
        raise HTTPException(status_code=404, detail=f"محطة المغادرة رقم {route.departure_station_id} غير موجودة")
    
    # ✅ التحقق من وجود محطة الوصول
    arrival_station = stations_crud.get_station(db, route.arrival_station_id)
    if not arrival_station:
        raise HTTPException(status_code=404, detail=f"محطة الوصول رقم {route.arrival_station_id} غير موجودة")
    
    return trips_crud.create_route(db, route)

@router.post("/prices", response_model=PricingHistoryResponse, dependencies=[Depends(get_current_admin)])
def create_pricing(pricing: PricingHistoryCreate, db: Session = Depends(get_db)):
    return trips_crud.create_pricing(db, pricing)

@router.get("/", response_model=List[TripResponse], dependencies=[Depends(get_current_admin)])
def get_trips(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return trips_crud.get_trips(db, skip=skip, limit=limit)

@router.get("/search")
def search_trips(
    departure_station_id: int = Query(...),
    arrival_station_id: int = Query(...),
    date: datetime = Query(...),
    db: Session = Depends(get_db)
):
    trips = trips_crud.get_available_trips(db, departure_station_id, arrival_station_id, date)
    result = []
    for trip in trips:
        available_seats = trip.total_seats - len(trip.bookings)
        dep = trip.route.departure_station
        arr = trip.route.arrival_station

        dep_name_ar = dep.name
        dep_name_en = dep.name_en or dep.name
        arr_name_ar = arr.name
        arr_name_en = arr.name_en or arr.name

        result.append({
            "id": trip.id,
            "route": f"{dep_name_ar} → {arr_name_ar}",
            "route_en": f"{dep_name_en} → {arr_name_en}",
            "departure_station_name": dep_name_ar,
            "departure_station_name_en": dep_name_en,
            "arrival_station_name": arr_name_ar,
            "arrival_station_name_en": arr_name_en,
            "bus_number": trip.bus.plate_number,
            "departure_time": trip.departure_time,
            "price": trip.price_at_time,
            "total_seats": trip.total_seats,
            "available_seats": available_seats
        })
    return result

@router.delete("/routes/{route_id}", dependencies=[Depends(get_current_admin)])
def delete_route(route_id: int, db: Session = Depends(get_db)):
    route = trips_crud.get_route(db, route_id)
    if not route:
        raise HTTPException(status_code=404, detail="المسار غير موجود")
    
    # التحقق من وجود رحلات مرتبطة
    trips = db.query(Trip).filter(Trip.route_id == route_id).all()
    if trips:
        raise HTTPException(status_code=400, detail="لا يمكن حذف المسار لوجود رحلات مرتبطة به")
    
    db.delete(route)
    db.commit()
    return {"message": f"تم حذف المسار {route_id} بنجاح"}

@router.post("/", response_model=TripResponse, dependencies=[Depends(get_current_admin)])
def create_trip(trip: TripCreate, db: Session = Depends(get_db)):
    route = trips_crud.get_route(db, trip.route_id)
    if not route:
        raise HTTPException(status_code=404, detail="المسار غير موجود")
    latest_price = trips_crud.get_pricing_history(db, trip.route_id)
    if not latest_price and trip.price_at_time is None:
        raise HTTPException(status_code=400, detail="لا يوجد سعر محدد لهذا المسار، يرجى إضافة سعر أولاً")
    try:
        return trips_crud.create_trip(db, trip)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{trip_id}", response_model=TripResponse, dependencies=[Depends(get_current_admin)])
def update_trip_endpoint(trip_id: int, trip: TripCreate, db: Session = Depends(get_db)):
    """تعديل رحلة (السائق، المساعد، حالة النشاط)"""
    try:
        updated = trips_crud.update_trip(db, trip_id, trip)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not updated:
        raise HTTPException(status_code=404, detail="الرحلة غير موجودة")
    return updated


@router.put("/{trip_id}/status", dependencies=[Depends(get_current_admin)])
def update_trip_status(trip_id: int, is_active: bool, db: Session = Depends(get_db)):
    trip = trips_crud.update_trip_status(db, trip_id, is_active)
    if not trip:
        raise HTTPException(status_code=404, detail="الرحلة غير موجودة")
    return {"message": f"تم تحديث حالة الرحلة إلى {is_active}"}

@router.delete("/{trip_id}", dependencies=[Depends(get_current_admin)])
def delete_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = trips_crud.get_trip(db, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="الرحلة غير موجودة")
    from app.crud import bookings_crud
    bookings = bookings_crud.get_bookings_by_trip(db, trip_id)
    if bookings:
        raise HTTPException(status_code=400, detail="لا يمكن حذف الرحلة لأنها تحتوي على حجوزات")
    db.delete(trip)
    db.commit()
    return {"message": f"تم حذف الرحلة رقم {trip_id} بنجاح"}