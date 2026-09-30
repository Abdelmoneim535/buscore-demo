# -*- coding: utf-8 -*-
"""
auth_utils.py  المصادقة والأمان
- استخدام bcrypt مباشرة (بدون passlib)
- توليد والتحقق من JWT
- إدارة الكوكيز
"""
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import os
from dotenv import load_dotenv

load_dotenv()

# 
# الإعدادات
# 
SECRET_KEY = os.getenv("SECRET_KEY", "buscore-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # أسبوع
COOKIE_NAME = "buscore_token"


# 
# كلمات المرور (bcrypt)
# 
def get_password_hash(password: str) -> str:
    """تشفير كلمة المرور باستخدام bcrypt"""
    if not password:
        raise ValueError("كلمة المرور فارغة")
    # bcrypt يحد من الطول إلى 72 بايت
    password_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """التحقق من كلمة المرور"""
    if not plain_password or not hashed_password:
        return False
    try:
        password_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception as e:
        print(f"  خطأ في التحقق من كلمة المرور: {e}")
        return False


# 
# JWT
# 
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """إنشاء JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """فك تشفير JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        print(f"  خطأ في فك التشفير: {e}")
        return None


def extract_username_from_token(token: str) -> Optional[str]:
    """استخراج اسم المستخدم من token"""
    payload = decode_token(token)
    if not payload:
        return None
    return payload.get("sub") or payload.get("username")


# 
# تصدير
# 
__all__ = [
    "get_password_hash",
    "verify_password",
    "create_access_token",
    "decode_token",
    "extract_username_from_token",
    "COOKIE_NAME",
    "SECRET_KEY",
    "ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
]
