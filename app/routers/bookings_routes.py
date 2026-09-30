from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database.database import get_db
from app.routers.auth_routes import get_current_admin
from app.crud import bookings_crud
from app.schemas.bookings_schemas import (
    BookingCreate, BookingResponse, BookingUpdateStatus,
    PassengerCreate, PassengerResponse,
    LuggageCreate, LuggageResponse,
    GroupBookingCreate, GroupBookingResponse,
)
from app.models.bookings_models import BookingStatus

router = APIRouter(prefix="/bookings", tags=["الحجوزات"])

@router.get("/passengers", response_model=List[PassengerResponse], dependencies=[Depends(get_current_admin)])
def get_passengers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return bookings_crud.get_passengers(db, skip=skip, limit=limit)

@router.post("/passengers", response_model=PassengerResponse)
def create_passenger(passenger: PassengerCreate, db: Session = Depends(get_db)):
    # ✅ السماح بإنشاء راكب جديد حتى لو كان رقم الهاتف موجوداً
    # لا نقوم بالتحقق من وجود الرقم مسبقاً
    return bookings_crud.create_passenger(db, passenger)

@router.get("/passengers/{passenger_id}", response_model=PassengerResponse, dependencies=[Depends(get_current_admin)])
def get_passenger(passenger_id: int, db: Session = Depends(get_db)):
    passenger = bookings_crud.get_passenger(db, passenger_id)
    if not passenger:
        raise HTTPException(status_code=404, detail="الراكب غير موجود")
    return passenger

@router.get("/luggage", response_model=List[LuggageResponse])
def get_luggage(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return bookings_crud.get_all_luggage(db, skip=skip, limit=limit)

@router.post("/luggage", response_model=LuggageResponse, dependencies=[Depends(get_current_admin)])
def create_luggage(luggage: LuggageCreate, db: Session = Depends(get_db)):
    return bookings_crud.create_luggage(db, luggage)

@router.put("/luggage/{luggage_id}", response_model=LuggageResponse, dependencies=[Depends(get_current_admin)])
def update_luggage(luggage_id: int, luggage: LuggageCreate, db: Session = Depends(get_db)):
    updated = bookings_crud.update_luggage(db, luggage_id, luggage)
    if not updated:
        raise HTTPException(status_code=404, detail="الأمتعة غير موجودة")
    return updated

@router.delete("/luggage/{luggage_id}", dependencies=[Depends(get_current_admin)])
def delete_luggage(luggage_id: int, db: Session = Depends(get_db)):
    deleted = bookings_crud.delete_luggage(db, luggage_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="الأمتعة غير موجودة")
    return {"message": f"تم حذف الأمتعة رقم {luggage_id} بنجاح"}

@router.get("/", response_model=List[BookingResponse], dependencies=[Depends(get_current_admin)])
def get_bookings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return bookings_crud.get_bookings(db, skip=skip, limit=limit)

# ============================================================
# ✅ Group Booking (PNR) - الحجز الجماعي
# ============================================================

@router.post("/group", response_model=GroupBookingResponse)
def create_group_booking(group: GroupBookingCreate, db: Session = Depends(get_db)):
    """
    إنشاء حجز جماعي (عائلة) برقم PNR واحد + رقم تذكرة لكل راكب
    """
    if not group.items:
        raise HTTPException(status_code=400, detail="يجب إضافة راكب واحد على الأقل")

    result = bookings_crud.create_booking_group(db, group)

    # ✅ إذا رجع dict فيه error (نافذة الحجز مغلقة)
    if isinstance(result, dict) and result.get("error"):
        error_type = result.get("error_type", "unknown")
        message = result.get("message", "فشل إنشاء الحجز")

        if error_type == "booking_window_closed":
            raise HTTPException(
                status_code=403,
                detail={
                    "error_type": "booking_window_closed",
                    "message": message,
                    "minutes_left": result.get("minutes_left", 0),
                }
            )
        else:
            raise HTTPException(status_code=400, detail=message)

    if not result:
        raise HTTPException(
            status_code=400,
            detail="فشل إنشاء الحجز الجماعي — تحقق من البيانات والمقاعد المتاحة"
        )
    return result


@router.get("/pnr/{pnr}", response_model=List[BookingResponse])
def get_bookings_by_pnr(pnr: str, db: Session = Depends(get_db)):
    """جلب كل حجوزات مجموعة معينة بواسطة PNR"""
    bookings = bookings_crud.get_bookings_by_pnr(db, pnr)
    if not bookings:
        raise HTTPException(status_code=404, detail="PNR غير موجود")
    return bookings


@router.get("/{booking_id}", response_model=BookingResponse, dependencies=[Depends(get_current_admin)])
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = bookings_crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="الحجز غير موجود")
    return booking

@router.get("/reference/{reference}", response_model=BookingResponse)
def get_booking_by_reference(reference: str, db: Session = Depends(get_db)):
    booking = bookings_crud.get_booking_by_reference(db, reference)
    if not booking:
        raise HTTPException(status_code=404, detail="الحجز غير موجود")
    return booking

@router.get("/trip/{trip_id}", response_model=List[BookingResponse], dependencies=[Depends(get_current_admin)])
def get_bookings_by_trip(trip_id: int, db: Session = Depends(get_db)):
    return bookings_crud.get_bookings_by_trip(db, trip_id)

@router.post("/", response_model=BookingResponse)
def create_booking(booking: BookingCreate, db: Session = Depends(get_db)):
    passenger = bookings_crud.get_passenger(db, booking.passenger_id)
    if not passenger:
        raise HTTPException(status_code=404, detail="الراكب غير موجود")
    
    available_seats = bookings_crud.get_available_seats(db, booking.trip_id)
    if available_seats < len(booking.seat_numbers):
        raise HTTPException(status_code=400, detail=f"لا توجد مقاعد كافية. المتاح: {available_seats}, المطلوب: {len(booking.seat_numbers)}")
    
    new_booking = bookings_crud.create_booking(db, booking)
    if not new_booking:
        raise HTTPException(status_code=400, detail="فشل إنشاء الحجز")
    
    return new_booking

@router.patch("/{booking_id}/status", dependencies=[Depends(get_current_admin)])
def update_booking_status(booking_id: int, status_update: BookingUpdateStatus, db: Session = Depends(get_db)):
    booking = bookings_crud.update_booking_status(db, booking_id, status_update.status)
    if not booking:
        raise HTTPException(status_code=404, detail="الحجز غير موجود")
    return {"message": f"تم تحديث حالة الحجز إلى {status_update.status.value}"}

@router.delete("/{booking_id}", dependencies=[Depends(get_current_admin)])
def cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = bookings_crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="الحجز غير موجود")
    if booking.status == BookingStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="الحجز ملغى بالفعل")
    cancelled_booking = bookings_crud.cancel_booking(db, booking_id)
    if not cancelled_booking:
        raise HTTPException(status_code=400, detail="فشل إلغاء الحجز")
    return {"message": "تم إلغاء الحجز بنجاح", "booking_reference": cancelled_booking.booking_reference, "status": cancelled_booking.status.value}

@router.post("/{booking_id}/confirm", dependencies=[Depends(get_current_admin)])
def confirm_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = bookings_crud.confirm_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="الحجز غير موجود")
    return {"message": "تم تأكيد الحجز بنجاح"}

@router.get("/passenger/{passenger_id}", response_model=List[BookingResponse], dependencies=[Depends(get_current_admin)])
def get_passenger_bookings(passenger_id: int, db: Session = Depends(get_db)):
    return bookings_crud.get_booking_by_passenger(db, passenger_id)

@router.get("/available-seats/{trip_id}")
def get_available_seats(trip_id: int, db: Session = Depends(get_db)):
    available = bookings_crud.get_available_seats(db, trip_id)
    booked_seats = bookings_crud.get_booked_seat_numbers(db, trip_id)
    return {
        "trip_id": trip_id,
        "available_seats": available,
        "booked_seat_numbers": booked_seats  # ✅ قائمة أرقام المقاعد المحجوزة
    }