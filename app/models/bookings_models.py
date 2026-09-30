from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, JSON, Enum, Table, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database.database import Base

class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class BookingType(str, enum.Enum):
    ONLINE = "online"
    OFFICE = "office"

#  جدول وسيط مع quantity (Association Object)
class BookingLuggage(Base):
    __tablename__ = "booking_luggage"
    
    booking_id = Column(Integer, ForeignKey("bookings.id"), primary_key=True)
    luggage_id = Column(Integer, ForeignKey("luggage.id"), primary_key=True)
    quantity = Column(Integer, default=1, nullable=False)
    
    booking = relationship("Booking", back_populates="luggage_associations")
    luggage = relationship("Luggage")

class Passenger(Base):
    __tablename__ = "passengers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(100), nullable=True)
    id_number = Column(String(50), nullable=True)
    age = Column(Integer, nullable=True)
    is_infant = Column(Boolean, default=False)
    #  الربط بالعميل (الحاجز)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    bookings = relationship("Booking", back_populates="passenger")
    customer = relationship("Customer", back_populates="passengers")


class Luggage(Base):
    __tablename__ = "luggage"

    id = Column(Integer, primary_key=True, index=True)
    luggage_type = Column(String(20), nullable=False)
    weight_kg = Column(Integer, nullable=False)      # ✅ تأكد من وجود هذا السطر
    price = Column(Numeric(8, 2), nullable=False)
    is_free = Column(Boolean, default=False)         # ✅ تأكد من وجود هذا السطر
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    bookings = relationship("BookingLuggage", back_populates="luggage")

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    passenger_id = Column(Integer, ForeignKey("passengers.id"), nullable=False)
    seat_numbers = Column(JSON, nullable=False)
    infant_count = Column(Integer, default=0)
    booking_type = Column(Enum(BookingType), nullable=False)
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    total_price = Column(Numeric(12, 2), nullable=False)
    booking_reference = Column(String(20), unique=True, nullable=False)
    # ✅ رقم الحجز العائلي/الجماعي (PNR)
    pnr_reference = Column(String(30), nullable=True, index=True)
    # ✅ رقم التذكرة الفردي (TKT-xxxx)
    ticket_number = Column(String(30), nullable=True, unique=True, index=True)
    booked_at = Column(DateTime(timezone=True), server_default=func.now())
    
    @property
    def luggage_items(self):
        """للتوافق: يعيد قائمة Luggage (مع تكرار حسب quantity)"""
        result = []
        for assoc in self.luggage_associations:
            for _ in range(assoc.quantity):
                result.append(assoc.luggage)
        return result

    #  الفروع والحجز الذاتي
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)
    booking_source = Column(String(20), nullable=True, default="office")  # office / app / web
    booking_channel = Column(String(20), nullable=True)  # للتفاصيل

    trip = relationship("Trip", back_populates="bookings")
    passenger = relationship("Passenger", back_populates="bookings")
    luggage_associations = relationship("BookingLuggage", back_populates="booking", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="booking", uselist=False)
    branch = relationship("Branch", back_populates="bookings")
    customer = relationship("Customer", back_populates="bookings")