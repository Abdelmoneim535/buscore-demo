# -*- coding: utf-8 -*-
"""سجل التدقيق للقيود"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.database.database import Base


class JournalEntryAudit(Base):
    """سجل تدقيق  كل تعديل على قيد"""
    __tablename__ = "journal_entry_audit"

    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, nullable=True, index=True)
    action = Column(String(30), nullable=False)  # create/update/post/unpost/reverse/delete
    old_value = Column(Text, nullable=True)      # JSON
    new_value = Column(Text, nullable=True)      # JSON
    performed_by = Column(Integer, nullable=True)
    performed_at = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45), nullable=True)
    notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"<JournalEntryAudit entry={self.entry_id} action={self.action}>"
