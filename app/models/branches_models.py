from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base


class Branch(Base):
    """الفروع (المركز الرئيسي + الفروع الفرعية)"""
    __tablename__ = "branches"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=True)
    address = Column(Text, nullable=True)
    address_en = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    manager_name = Column(String(200), nullable=True)
    manager_phone = Column(String(20), nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # العلاقات
    city = relationship("City", foreign_keys=[city_id])
    bookings = relationship("Booking", back_populates="branch")
    users = relationship("User", back_populates="branch")
    employees = relationship("Employee", back_populates="branch")
    expenses = relationship("Expense", back_populates="branch")
    trips = relationship("Trip", back_populates="branch")
    customers = relationship("Customer", back_populates="preferred_branch")

    def __repr__(self):
        return f"<Branch {self.code} - {self.name}>"
