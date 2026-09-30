from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database.database import get_db
from app.routers.auth_routes import get_current_admin
from app.crud import stations_crud
from app.schemas.stations_schemas import CityCreate, CityResponse, StationCreate, StationResponse

router = APIRouter(prefix="/stations", tags=["المدن والمحطات"])

@router.get("/cities", response_model=List[CityResponse])
def get_cities(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return stations_crud.get_cities(db, skip=skip, limit=limit)

@router.post("/cities", response_model=CityResponse, dependencies=[Depends(get_current_admin)])
def create_city(city: CityCreate, db: Session = Depends(get_db)):
    result = stations_crud.create_city(db, city)
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@router.put("/cities/{city_id}", response_model=CityResponse, dependencies=[Depends(get_current_admin)])
def update_city(city_id: int, city: CityCreate, db: Session = Depends(get_db)):
    updated = stations_crud.update_city(db, city_id, city)
    if not updated:
        raise HTTPException(status_code=404, detail="المدينة غير موجودة")
    return updated

@router.delete("/cities/{city_id}", dependencies=[Depends(get_current_admin)])
def delete_city(city_id: int, db: Session = Depends(get_db)):
    city = stations_crud.delete_city(db, city_id)
    if not city:
        raise HTTPException(status_code=404, detail="المدينة غير موجودة")
    return {"message": "تم حذف المدينة بنجاح"}

@router.get("/", response_model=List[StationResponse])
def get_stations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return stations_crud.get_stations(db, skip=skip, limit=limit)

@router.post("/", response_model=StationResponse, dependencies=[Depends(get_current_admin)])
def create_station(station: StationCreate, db: Session = Depends(get_db)):
    result = stations_crud.create_station(db, station)
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@router.put("/{station_id}", response_model=StationResponse, dependencies=[Depends(get_current_admin)])
def update_station(station_id: int, station: StationCreate, db: Session = Depends(get_db)):
    updated = stations_crud.update_station(db, station_id, station)
    if not updated:
        raise HTTPException(status_code=404, detail="المحطة غير موجودة")
    return updated


@router.delete("/{station_id}", dependencies=[Depends(get_current_admin)])
def delete_station(station_id: int, db: Session = Depends(get_db)):
    station = stations_crud.delete_station(db, station_id)
    if not station:
        raise HTTPException(status_code=404, detail="المحطة غير موجودة")
    return {"message": "تم حذف المحطة بنجاح"}