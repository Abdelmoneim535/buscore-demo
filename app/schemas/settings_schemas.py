from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CompanySettingsBase(BaseModel):
    company_name: str = "BusCore"
    company_name_en: Optional[str] = None
    company_logo: Optional[str] = None
    company_phone: Optional[str] = None
    company_email: Optional[str] = None
    company_address: Optional[str] = None
    company_address_en: Optional[str] = None
    company_website: Optional[str] = None
    tax_number: Optional[str] = None
    commercial_register: Optional[str] = None
    ticket_footer_text: Optional[str] = None
    ticket_footer_text_en: Optional[str] = None
    ticket_instructions: Optional[str] = None
    ticket_instructions_en: Optional[str] = None
    ticket_warranty_text: Optional[str] = None
    ticket_warranty_text_en: Optional[str] = None
    bank_name: Optional[str] = None
    bank_name_en: Optional[str] = None
    bank_account: Optional[str] = None
    bank_account_name: Optional[str] = None
    bank_account_name_en: Optional[str] = None
    support_phone: Optional[str] = None
    support_whatsapp: Optional[str] = None
    primary_color: Optional[str] = "#0d6efd"
    secondary_color: Optional[str] = "#6c757d"


class CompanySettingsCreate(CompanySettingsBase):
    pass


class CompanySettingsResponse(CompanySettingsBase):
    id: int
    updated_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True