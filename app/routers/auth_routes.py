from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional, List
from jose import JWTError, jwt
from app.database.database import get_db
from app.crud import user_crud
from app.schemas.user_schemas import UserCreate, UserResponse, Token
from app.auth_utils import (
    create_access_token, decode_token, extract_username_from_token,
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, COOKIE_NAME,
)

router = APIRouter(prefix="/auth", tags=["المصادقة"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


# 
# دوال مساعدة
# 

def _get_token_from_request(request: Request, bearer_token: Optional[str] = None) -> Optional[str]:
    """استخراج الـ token من Cookie أو Header"""
    # 1) من Cookie
    token = request.cookies.get(COOKIE_NAME)
    if token:
        return token
    # 2) من Authorization header (backward compatibility)
    if bearer_token:
        return bearer_token
    return None


# 
# Dependency: المستخدم الحالي (محمي)
# 

def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """جلب المستخدم الحالي من Cookie أو Bearer token"""
    final_token = _get_token_from_request(request, token)
    if not final_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="غير مصرح  يجب تسجيل الدخول",
        )
    username = extract_username_from_token(final_token)
    if not username:
        raise HTTPException(status_code=401, detail="جلسة غير صالحة")

    user = user_crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=401, detail="المستخدم غير موجود")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="الحساب موقوف")
    return user


def get_current_admin(
    user = Depends(get_current_user),
):
    """Dependency: للمديرين فقط"""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="هذه الصفحة للمديرين فقط")
    return user


# 
# Endpoints
# 

@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    if len(user.password) > 72:
        raise HTTPException(status_code=400, detail="كلمة المرور طويلة جداً (الحد الأقصى 72 حرفاً)")
    existing_user = user_crud.get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="اسم المستخدم موجود بالفعل")
    existing_email = user_crud.get_user_by_email(db, user.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="البريد الإلكتروني موجود بالفعل")
    return user_crud.create_user(db, user)


@router.post("/login", response_model=Token)
def login_user(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = user_crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="اسم المستخدم أو كلمة المرور غير صحيحة",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="الحساب موقوف  راجع المدير")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "is_admin": user.is_admin},
        expires_delta=access_token_expires,
    )

    #  ضع الـ Cookie كـ httpOnly (آمن)
    response.set_cookie(
        key=COOKIE_NAME,
        value=access_token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,           # لا يمكن قراءتها بـ JavaScript
        samesite="lax",          # حماية من CSRF
        secure=False,            #  اجعلها True عند النشر بـ HTTPS
        path="/",
    )

    #  نُبقي الـ token في الـ response للتوافق مع الكود القديم
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout_user(response: Response):
    """تسجيل خروج  يحذف الـ Cookie"""
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"message": "تم تسجيل الخروج بنجاح"}


@router.get("/me", response_model=UserResponse)
def get_me(user = Depends(get_current_user)):
    """المستخدم الحالي"""
    return user


# 
# إدارة المستخدمين (للمدير فقط)
# 

@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    skip: int = 0,
    limit: int = 100,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    users = db.query(user_crud.User).offset(skip).limit(limit).all()
    return users


@router.post("/users", response_model=UserResponse)
def create_new_user(
    user: UserCreate,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if len(user.password) > 72:
        raise HTTPException(status_code=400, detail="كلمة المرور طويلة جداً")
    existing_user = user_crud.get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="اسم المستخدم موجود بالفعل")
    existing_email = user_crud.get_user_by_email(db, user.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="البريد الإلكتروني موجود بالفعل")
    return user_crud.create_user(db, user)


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserCreate,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(user_crud.User).filter(user_crud.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    user.username = user_data.username
    user.email = user_data.email
    if user_data.password:
        user.hashed_password = user_crud.hash_password(user_data.password)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(user_crud.User).filter(user_crud.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    db.delete(user)
    db.commit()
    return {"message": "تم حذف المستخدم بنجاح"}


@router.patch("/users/{user_id}/status")
def toggle_user_status(
    user_id: int,
    is_active: bool,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(user_crud.User).filter(user_crud.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return {"message": f"تم تحديث حالة المستخدم إلى {'نشط' if is_active else 'متوقف'}"}
