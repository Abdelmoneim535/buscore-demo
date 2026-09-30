# -*- coding: utf-8 -*-
"""Router: إعدادات النظام المحاسبي"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict

from app.database.database import get_db
from app.routers.auth_routes import get_current_admin
from app.crud import accounting_settings_crud as asc
from app.schemas.accounting_settings_schemas import (
    AccountingSettingsResponse, AccountingSettingsUpdate,
)

router = APIRouter(prefix="/accounting-settings", tags=["إعدادات النظام المحاسبي"])


@router.get("/", response_model=AccountingSettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    """الإعدادات الحالية"""
    return asc.get_settings(db)


@router.get("/summary")
def get_settings_summary(db: Session = Depends(get_db)):
    """ملخص الإعدادات"""
    return asc.get_settings_summary(db)


@router.get("/features")
def get_enabled_features(db: Session = Depends(get_db)):
    """قائمة الميزات المفعّلة"""
    return asc.get_enabled_features(db)


@router.get("/check/{feature}")
def check_feature(feature: str, db: Session = Depends(get_db)):
    """فحص هل ميزة معيّنة مفعّلة"""
    return {"feature": feature, "enabled": asc.is_feature_enabled(db, feature)}


@router.put("/", response_model=AccountingSettingsResponse, dependencies=[Depends(get_current_admin)])
def update_settings(data: AccountingSettingsUpdate, db: Session = Depends(get_db)):
    """تعديل الإعدادات"""
    result = asc.update_settings(db, data)
    if not result:
        raise HTTPException(status_code=404, detail="الإعدادات غير موجودة")
    return result


@router.post("/tier/{tier}", response_model=AccountingSettingsResponse, dependencies=[Depends(get_current_admin)])
def apply_tier(tier: str, db: Session = Depends(get_db)):
    """تطبيق مستوى جاهز (simple/medium/full)"""
    result = asc.apply_tier(db, tier)
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/reset", response_model=AccountingSettingsResponse, dependencies=[Depends(get_current_admin)])
def reset_settings(db: Session = Depends(get_db)):
    """إعادة للافتراضي"""
    return asc.reset_settings(db)
