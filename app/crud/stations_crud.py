from sqlalchemy.orm import Session
from app.models.stations_models import City, Station
from app.schemas.stations_schemas import CityCreate, StationCreate


def get_city(db: Session, city_id: int):
    return db.query(City).filter(City.id == city_id).first()


def get_cities(db: Session, skip: int = 0, limit: int = 100):
    return db.query(City).offset(skip).limit(limit).all()


def create_city(db: Session, city: CityCreate):
    #  التحقق من اسم المدينة
    existing_name = db.query(City).filter(City.name == city.name).first()
    if existing_name:
        return {"error": "name_duplicate", "message": f"المدينة '{city.name}' موجودة مسبقًا"}

    #  التحقق من كود IATA
    existing_code = db.query(City).filter(City.code == city.code.upper()).first()
    if existing_code:
        return {"error": "code_duplicate", "message": f"كود IATA '{city.code}' مستخدم مسبقًا للمدينة: {existing_code.name}"}

    db_city = City(
        name=city.name,
        name_en=city.name_en,
        code=city.code.upper()
    )
    db.add(db_city)
    db.commit()
    db.refresh(db_city)
    return db_city


def update_city(db: Session, city_id: int, city: CityCreate):
    db_city = get_city(db, city_id)
    if not db_city:
        return None
    db_city.name = city.name
    db_city.name_en = city.name_en
    db_city.code = city.code
    db.commit()
    db.refresh(db_city)
    return db_city


def delete_city(db: Session, city_id: int):
    city = get_city(db, city_id)
    if city:
        db.delete(city)
        db.commit()
    return city


def get_station(db: Session, station_id: int):
    return db.query(Station).filter(Station.id == station_id).first()


def get_stations(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Station).offset(skip).limit(limit).all()


def create_station(db: Session, station: StationCreate):
    #  التحقق من وجود المدينة
    from app.models.stations_models import City as CityModel
    city = db.query(CityModel).filter(CityModel.id == station.city_id).first()
    if not city:
        return {"error": "city_not_found", "message": "المدينة غير موجودة"}

    #  التحقق من اسم المحطة (في نفس المدينة)
    existing = db.query(Station).filter(
        Station.name == station.name,
        Station.city_id == station.city_id
    ).first()
    if existing:
        return {"error": "name_duplicate", "message": f"المحطة '{station.name}' موجودة مسبقًا في {city.name}"}

    db_station = Station(
        name=station.name,
        name_en=station.name_en,
        city_id=station.city_id,
        address=station.address,
        address_en=station.address_en,
        phone=station.phone
    )
    db.add(db_station)
    db.commit()
    db.refresh(db_station)
    return db_station


def update_station(db: Session, station_id: int, station: StationCreate):
    db_station = get_station(db, station_id)
    if not db_station:
        return None
    db_station.name = station.name
    db_station.name_en = station.name_en
    db_station.city_id = station.city_id
    db_station.address = station.address
    db_station.address_en = station.address_en
    db_station.phone = station.phone
    db.commit()
    db.refresh(db_station)
    return db_station


def delete_station(db: Session, station_id: int):
    station = get_station(db, station_id)
    if station:
        db.delete(station)
        db.commit()
    return station