# -*- coding: utf-8 -*-
"""Schemas: سجل التدقيق"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class JournalEntryAuditResponse(BaseModel):
    id: int
    entry_id: Optional[int] = None
    action: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    performed_by: Optional[int] = None
    performed_at: datetime
    ip_address: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True
