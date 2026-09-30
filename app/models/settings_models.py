from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database.database import Base


class CompanySettings(Base):
    __tablename__ = "company_settings"

    id = Column(Integer, primary_key=True, index=True)

    # معلومات الشركة
    company_name = Column(String(200), nullable=False, default="BusCore")
    company_name_en = Column(String(200), nullable=True)
    company_logo = Column(String(500), nullable=True)
    company_phone = Column(String(50), nullable=True)
    company_email = Column(String(100), nullable=True)
    company_address = Column(Text, nullable=True)          # العنوان بالعربي
    company_address_en = Column(Text, nullable=True)       # العنوان بالإنجليزي
    company_website = Column(String(200), nullable=True)

    # السجل التجاري والرقم الضريبي (عالمية)
    tax_number = Column(String(50), nullable=True)
    commercial_register = Column(String(50), nullable=True)

    # إعدادات التذكرة (عربي + إنجليزي)
    ticket_footer_text = Column(Text, nullable=True, default="شكراً لثقتكم بنا")
    ticket_footer_text_en = Column(Text, nullable=True)
    ticket_instructions = Column(Text, nullable=True,
        default="⏰ الحضور قبل 30 دقيقة\n🆔 إحضار إثبات الهوية\n🧳 الوزن المسموح 40 كجم")
    ticket_instructions_en = Column(Text, nullable=True)
    ticket_warranty_text = Column(Text, nullable=True,
        default="يجب إظهار التذكرة عند الصعود")
    ticket_warranty_text_en = Column(Text, nullable=True)

    # معلومات الدفع
    bank_name = Column(String(100), nullable=True)
    bank_name_en = Column(String(100), nullable=True)
    bank_account = Column(String(100), nullable=True)
    bank_account_name = Column(String(200), nullable=True)
    bank_account_name_en = Column(String(200), nullable=True)

    # الدعم (عالمية)
    support_phone = Column(String(50), nullable=True)
    support_whatsapp = Column(String(50), nullable=True)

    # الألوان
    primary_color = Column(String(20), default="#0d6efd")
    secondary_color = Column(String(20), default="#6c757d")

    # التحديثات
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())