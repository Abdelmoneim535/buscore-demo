# -*- coding: utf-8 -*-
"""مراكز التكلفة"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base


class CostCenter(Base):
    """مركز تكلفة (فرع / باص / رحلة / قسم)"""
    __tablename__ = "cost_centers"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=True)
    center_type = Column(String(30), nullable=False)  # branch / bus / trip / department / project
    reference_id = Column(Integer, nullable=True)      # branch_id / bus_id / trip_id
    parent_id = Column(Integer, ForeignKey("cost_centers.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    parent = relationship("CostCenter", remote_side=[id], backref="children")

    def __repr__(self):
        return f"<CostCenter {self.code} - {self.name}>"
