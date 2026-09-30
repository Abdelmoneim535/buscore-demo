from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base


class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    name_en = Column(String(100), nullable=True)
    code = Column(String(3), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    stations = relationship("Station", back_populates="city")

    def __repr__(self):
        return f"<City {self.code} - {self.name}>"


class Station(Base):
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    address = Column(Text, nullable=True)
    address_en = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    city = relationship("City", back_populates="stations")
    departure_routes = relationship("Route", foreign_keys="Route.departure_station_id", back_populates="departure_station")
    arrival_routes = relationship("Route", foreign_keys="Route.arrival_station_id", back_populates="arrival_station")