from sqlalchemy.orm import Session
from app.models.settings_models import CompanySettings
from app.schemas.settings_schemas import CompanySettingsCreate

def get_settings(db: Session):
    """إرجاع الإعدادات، وإنشاء إعدادات افتراضية إذا لم توجد"""
    settings = db.query(CompanySettings).first()
    if not settings:
        settings = CompanySettings(company_name="BusCore")
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

def update_settings(db: Session, data: CompanySettingsCreate):
    """تحديث الإعدادات"""
    settings = get_settings(db)
    for key, value in data.dict(exclude_unset=True).items():
        setattr(settings, key, value)
    db.commit()
    db.refresh(settings)
    return settings