from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base


class Bus(Base):
    __tablename__ = "buses"

    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String(20), unique=True, nullable=False, index=True)
    model = Column(String(100), nullable=False)
    total_seats = Column(Integer, nullable=False)
    year = Column(Integer, nullable=True)
    color = Column(String(50), nullable=True)
    color_en = Column(String(50), nullable=True)
    image_url = Column(String(500), nullable=True)
    video_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    trips = relationship("Trip", back_populates="bus")

    def __repr__(self):
        return f"<Bus {self.plate_number} - {self.model}>"
