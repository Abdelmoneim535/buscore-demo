from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.routers.auth_routes import get_current_admin
from app.crud import settings_crud
from app.schemas.settings_schemas import CompanySettingsCreate, CompanySettingsResponse

router = APIRouter(prefix="/settings", tags=["إعدادات الشركة"])

@router.get("/", response_model=CompanySettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    """جلب إعدادات الشركة"""
    return settings_crud.get_settings(db)

@router.put("/", response_model=CompanySettingsResponse, dependencies=[Depends(get_current_admin)])
def update_settings(data: CompanySettingsCreate, db: Session = Depends(get_db)):
    """تحديث إعدادات الشركة"""
    return settings_crud.update_settings(db, data)