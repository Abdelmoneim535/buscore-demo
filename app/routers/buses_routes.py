from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.database.database import get_db
from app.routers.auth_routes import get_current_admin
from app.crud import bus_crud
from app.schemas.bus_schemas import BusCreate, BusResponse

router = APIRouter(prefix="/buses", tags=["الحافلات"])

@router.get("/", response_model=List[BusResponse])
def get_buses(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = Query(False, description="عرض الحافلات النشطة فقط"),
    db: Session = Depends(get_db)
):
    return bus_crud.get_buses(db, skip=skip, limit=limit, active_only=active_only)

@router.get("/{bus_id}", response_model=BusResponse)
def get_bus(bus_id: int, db: Session = Depends(get_db)):
    bus = bus_crud.get_bus(db, bus_id)
    if not bus:
        raise HTTPException(status_code=404, detail="الحافلة غير موجودة")
    return bus

@router.post("/", response_model=BusResponse, dependencies=[Depends(get_current_admin)])
def create_bus(bus: BusCreate, db: Session = Depends(get_db)):
    existing = bus_crud.get_bus_by_plate(db, bus.plate_number)
    if existing:
        raise HTTPException(status_code=400, detail=f"الحافلة برقم اللوحة {bus.plate_number} موجودة مسبقاً")
    return bus_crud.create_bus(db, bus)

@router.put("/{bus_id}", response_model=BusResponse, dependencies=[Depends(get_current_admin)])
def update_bus(bus_id: int, bus: BusCreate, db: Session = Depends(get_db)):
    updated = bus_crud.update_bus(db, bus_id, bus)
    if not updated:
        raise HTTPException(status_code=404, detail="الحافلة غير موجودة")
    return updated

@router.delete("/{bus_id}", dependencies=[Depends(get_current_admin)])
def delete_bus(bus_id: int, db: Session = Depends(get_db)):
    bus = bus_crud.delete_bus(db, bus_id)
    if not bus:
        raise HTTPException(status_code=404, detail="الحافلة غير موجودة")
    return {"message": f"تم حذف الحافلة رقم {bus_id} بنجاح"}

@router.patch("/{bus_id}/status", dependencies=[Depends(get_current_admin)])
def toggle_bus_status(bus_id: int, is_active: bool, db: Session = Depends(get_db)):
    bus = bus_crud.toggle_bus_status(db, bus_id, is_active)
    if not bus:
        raise HTTPException(status_code=404, detail="الحافلة غير موجودة")
    return {"message": f"تم تحديث حالة الحافلة إلى {is_active}"}