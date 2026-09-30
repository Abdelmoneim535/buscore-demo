# -*- coding: utf-8 -*-
"""
إعدادات قاعدة البيانات
- يدعم PostgreSQL (على Render) + SQLite (محلياً)
- يفضّل demo.db إن وُجد (نسخة تجريبية)
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# 
# قراءة DATABASE_URL من البيئة
# 
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


# 
# دالة مسار قاعدة البيانات (SQLite)
# 
def _get_db_path():
    """
    يرجع مسار قاعدة البيانات:
    - يفضّل demo.db إن وُجد (وضع Demo)
    - وإلا buscore.db (الوضع العادي)
    """
    if getattr(sys, 'frozen', False):
        # نعمل من .exe  بجانب الـ .exe
        base = Path(sys.executable).parent
    else:
        # Python عادي  في جذر المشروع
        base = Path(__file__).resolve().parent.parent.parent

    # فضّل demo.db
    demo_db = base / "demo.db"
    if demo_db.exists():
        return demo_db
    
    return base / "buscore.db"


# 
# إنشاء Engine
# 
if DATABASE_URL:
    # PostgreSQL (Render / Production)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URL = DATABASE_URL
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
    )
    print(f" Database: PostgreSQL (Production)")
else:
    # SQLite (محلياً)  يستخدم demo.db إن وُجد
    _db_path = _get_db_path()
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{_db_path}"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    print(f" Database: SQLite ({_db_path.name})")


# 
# Session + Base
# 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency للـ FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
