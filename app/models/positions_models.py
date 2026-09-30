from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.database.database import Base


class Position(Base):
    """الوظائف (سائق، مساعد سائق، مضيف، محاسب...)"""
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)          # عربي
    name_en = Column(String(100), nullable=True)        # إنجليزي
    category = Column(String(20), nullable=False, default="other")
    # الفئات: driver | assistant | admin | other
    icon = Column(String(50), nullable=True, default="fa-briefcase")
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Position {self.name} ({self.category})>"
