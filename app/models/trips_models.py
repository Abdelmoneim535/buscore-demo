from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base


class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    departure_station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
    arrival_station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
    distance_km = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    departure_station = relationship("Station", foreign_keys=[departure_station_id], back_populates="departure_routes")
    arrival_station = relationship("Station", foreign_keys=[arrival_station_id], back_populates="arrival_routes")
    prices = relationship("PricingHistory", back_populates="route")
    trips = relationship("Trip", back_populates="route")


class PricingHistory(Base):
    __tablename__ = "pricing_history"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    effective_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    route = relationship("Route", back_populates="prices")


class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    bus_id = Column(Integer, ForeignKey("buses.id"), nullable=False)
    total_seats = Column(Integer, nullable=False)
    departure_time = Column(DateTime, nullable=False)
    arrival_time = Column(DateTime, nullable=True)
    price_at_time = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True)

    # ✅ طاقم الرحلة (السائق + المساعد)
    driver_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    assistant_id = Column(Integer, ForeignKey("employees.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    #  الفرع والبيع الإلكتروني
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    is_online_sellable = Column(Boolean, default=True)

    route = relationship("Route", back_populates="trips")
    bus = relationship("Bus", back_populates="trips")
    bookings = relationship("Booking", back_populates="trip")
    driver = relationship("Employee", foreign_keys=[driver_id])
    assistant = relationship("Employee", foreign_keys=[assistant_id])
    branch = relationship("Branch", back_populates="trips")
