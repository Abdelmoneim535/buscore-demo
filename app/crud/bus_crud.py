from sqlalchemy.orm import Session
from app.models.bus_models import Bus
from app.schemas.bus_schemas import BusCreate

def get_bus(db: Session, bus_id: int):
    return db.query(Bus).filter(Bus.id == bus_id).first()

def get_bus_by_plate(db: Session, plate_number: str):
    return db.query(Bus).filter(Bus.plate_number == plate_number).first()

def get_buses(db: Session, skip: int = 0, limit: int = 100, active_only: bool = False):
    query = db.query(Bus)
    if active_only:
        query = query.filter(Bus.is_active == True)
    return query.offset(skip).limit(limit).all()

def create_bus(db: Session, bus: BusCreate):
    db_bus = Bus(
        plate_number=bus.plate_number,
        model=bus.model,
        total_seats=bus.total_seats,
        year=bus.year,
        color=bus.color,
        color_en=bus.color_en,
        image_url=bus.image_url,
        video_url=bus.video_url,
        is_active=bus.is_active
    )
    db.add(db_bus)
    db.commit()
    db.refresh(db_bus)
    return db_bus

def update_bus(db: Session, bus_id: int, bus_update: BusCreate):
    bus = get_bus(db, bus_id)
    if not bus:
        return None

    # تحديث كل حقل بشكل صريح (أضمن طريقة)
    bus.plate_number = bus_update.plate_number
    bus.model = bus_update.model
    bus.total_seats = bus_update.total_seats
    bus.year = bus_update.year
    bus.color = bus_update.color
    bus.color_en = bus_update.color_en
    bus.image_url = bus_update.image_url
    bus.video_url = bus_update.video_url
    bus.is_active = bus_update.is_active

    db.commit()
    db.refresh(bus)
    return bus

def delete_bus(db: Session, bus_id: int):
    bus = get_bus(db, bus_id)
    if bus:
        db.delete(bus)
        db.commit()
    return bus

def toggle_bus_status(db: Session, bus_id: int, is_active: bool):
    bus = get_bus(db, bus_id)
    if bus:
        bus.is_active = is_active
        db.commit()
        db.refresh(bus)
    return bus
