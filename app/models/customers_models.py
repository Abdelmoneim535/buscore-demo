from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base


class Customer(Base):
    """العملاء (المسجلون في التطبيق أو الموقع)"""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_code = Column(String(20), unique=True, nullable=True, index=True)
    full_name = Column(String(200), nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    phone_secondary = Column(String(20), nullable=True, index=True)
    email = Column(String(100), nullable=True)
    id_number = Column(String(50), nullable=True)
    passport_number = Column(String(50), nullable=True, index=True)
    national_id = Column(String(50), nullable=True, index=True)
    birth_date = Column(DateTime(timezone=True), nullable=True)
    nationality = Column(String(50), nullable=True)
    preferred_branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    total_bookings = Column(Integer, default=0)
    total_tickets = Column(Integer, default=0)
    total_infants = Column(Integer, default=0)
    total_spent = Column(Numeric(12, 2), default=0)
    is_vip = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_booking_at = Column(DateTime(timezone=True), nullable=True)

    # العلاقات
    preferred_branch = relationship("Branch", back_populates="customers")
    bookings = relationship("Booking", back_populates="customer")
    passengers = relationship("Passenger", back_populates="customer")

    def __repr__(self):
        return f"<Customer {self.full_name} - {self.phone}>"
