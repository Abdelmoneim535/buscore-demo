# -*- coding: utf-8 -*-
"""CRUD لإعدادات النظام المحاسبي"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, List
from datetime import datetime

from app.models.accounting_settings_models import AccountingSettings
from app.schemas.accounting_settings_schemas import AccountingSettingsUpdate


# 
# المستويات الجاهزة (Tiers)
# 

TIER_PRESETS = {
    "simple": {
        "tier": "simple",
        "enable_double_entry": False,
        "enable_journal": False,
        "enable_ledger": False,
        "enable_trial_balance": False,
        "enable_balance_sheet": False,
        "enable_income_statement": True,
        "enable_depreciation": False,
        "enable_fiscal_periods": False,
        "enable_audit_log": False,
        "enable_cost_centers": False,
        "enable_tax": False,
        "enable_multi_currency": False,
    },
    "medium": {
        "tier": "medium",
        "enable_double_entry": True,
        "enable_journal": True,
        "enable_ledger": True,
        "enable_trial_balance": True,
        "enable_balance_sheet": False,
        "enable_income_statement": True,
        "enable_depreciation": False,
        "enable_fiscal_periods": False,
        "enable_audit_log": False,
        "enable_cost_centers": True,
        "enable_tax": False,
        "enable_multi_currency": False,
    },
    "full": {
        "tier": "full",
        "enable_double_entry": True,
        "enable_journal": True,
        "enable_ledger": True,
        "enable_trial_balance": True,
        "enable_balance_sheet": True,
        "enable_income_statement": True,
        "enable_depreciation": True,
        "enable_fiscal_periods": True,
        "enable_audit_log": True,
        "enable_cost_centers": True,
        "enable_tax": True,
        "enable_multi_currency": False,
    },
}


# 
# قراءة
# 

def get_settings(db: Session) -> Optional[AccountingSettings]:
    """جلب إعدادات النظام المحاسبي (الأولى)"""
    settings = db.query(AccountingSettings).first()
    if not settings:
        settings = create_default_settings(db)
    return settings


def get_settings_by_company(db: Session, company_id: int) -> Optional[AccountingSettings]:
    """جلب إعدادات شركة معينة"""
    return db.query(AccountingSettings).filter(
        AccountingSettings.company_id == company_id
    ).first()


# 
# إنشاء
# 

def create_default_settings(db: Session) -> AccountingSettings:
    """إنشاء إعدادات افتراضية (simple mode)"""
    settings = AccountingSettings(
        company_id=1,
        tier="simple",
        enable_double_entry=False,
        enable_journal=False,
        enable_ledger=False,
        enable_trial_balance=False,
        enable_balance_sheet=False,
        enable_income_statement=True,
        enable_depreciation=False,
        enable_fiscal_periods=False,
        enable_audit_log=False,
        enable_cost_centers=False,
        enable_tax=False,
        enable_multi_currency=False,
        vat_rate=0,
        income_tax_rate=0,
        sales_tax_rate=0,
        depreciation_method="straight_line",
        inventory_method="fifo",
        base_currency="SDG",
    )
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


# 
# تعديل
# 

def update_settings(db: Session, data: AccountingSettingsUpdate) -> Optional[AccountingSettings]:
    """تعديل جزئي للإعدادات"""
    settings = get_settings(db)
    if not settings:
        return None

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if hasattr(settings, key):
            setattr(settings, key, value)

    settings.updated_at = datetime.now()

    db.commit()
    db.refresh(settings)
    return settings


def apply_tier(db: Session, tier: str) -> Optional[AccountingSettings]:
    """تطبيق مستوى جاهز (simple / medium / full)"""
    if tier not in TIER_PRESETS:
        return {
            "error": "invalid_tier",
            "message": f"المستوى '{tier}' غير معروف  استخدم: simple, medium, full",
        }

    settings = get_settings(db)
    if not settings:
        return None

    preset = TIER_PRESETS[tier]
    for key, value in preset.items():
        if hasattr(settings, key):
            setattr(settings, key, value)

    settings.updated_at = datetime.now()

    db.commit()
    db.refresh(settings)
    return settings


def reset_settings(db: Session) -> Optional[AccountingSettings]:
    """إعادة الإعدادات للافتراضي (simple)"""
    settings = get_settings(db)
    if not settings:
        return None

    # إعادة كل الحقول للافتراضي
    settings.tier = "simple"
    settings.enable_double_entry = False
    settings.enable_journal = False
    settings.enable_ledger = False
    settings.enable_trial_balance = False
    settings.enable_balance_sheet = False
    settings.enable_income_statement = True
    settings.enable_depreciation = False
    settings.enable_fiscal_periods = False
    settings.enable_audit_log = False
    settings.enable_cost_centers = False
    settings.enable_tax = False
    settings.enable_multi_currency = False
    settings.vat_rate = 0
    settings.income_tax_rate = 0
    settings.sales_tax_rate = 0
    settings.updated_at = datetime.now()

    db.commit()
    db.refresh(settings)
    return settings


# 
# الفحص
# 

def is_feature_enabled(db: Session, feature: str) -> bool:
    """فحص هل ميزة معينة مفعّلة"""
    settings = get_settings(db)
    if not settings:
        return False

    # التحقق من وجود الحقل
    attr_name = f"enable_{feature}"
    if not hasattr(settings, attr_name):
        return False

    return bool(getattr(settings, attr_name))


def get_enabled_features(db: Session) -> Dict[str, bool]:
    """قائمة كل الميزات وحالتها"""
    settings = get_settings(db)
    if not settings:
        return {}

    features = [
        "double_entry", "journal", "ledger", "trial_balance",
        "balance_sheet", "income_statement", "depreciation",
        "fiscal_periods", "audit_log", "cost_centers", "tax",
        "multi_currency",
    ]

    result = {}
    for f in features:
        attr_name = f"enable_{f}"
        result[f] = bool(getattr(settings, attr_name, False))

    return result


def get_settings_summary(db: Session) -> Dict:
    """ملخص الإعدادات"""
    settings = get_settings(db)
    if not settings:
        return {}

    enabled = get_enabled_features(db)

    return {
        "tier": settings.tier,
        "base_currency": settings.base_currency,
        "vat_rate": float(settings.vat_rate or 0),
        "income_tax_rate": float(settings.income_tax_rate or 0),
        "sales_tax_rate": float(settings.sales_tax_rate or 0),
        "depreciation_method": settings.depreciation_method,
        "inventory_method": settings.inventory_method,
        "enabled_features": enabled,
        "enabled_count": sum(1 for v in enabled.values() if v),
        "total_features": len(enabled),
        "updated_at": settings.updated_at,
    }
