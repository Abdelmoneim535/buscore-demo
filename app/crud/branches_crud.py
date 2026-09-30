from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.branches_models import Branch
from app.schemas.branches_schemas import BranchCreate, BranchUpdate


# 
# قراءة
# 

def get_branch(db: Session, branch_id: int):
    """جلب فرع بالمعرف"""
    return db.query(Branch).filter(Branch.id == branch_id).first()


def get_branch_by_code(db: Session, code: str):
    """جلب فرع بالكود (BR-001)"""
    return db.query(Branch).filter(Branch.code == code).first()


def get_branches(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
) -> List[Branch]:
    """قائمة الفروع مع إمكانية الفلترة"""
    query = db.query(Branch)
    if is_active is not None:
        query = query.filter(Branch.is_active == is_active)
    return query.order_by(Branch.id).offset(skip).limit(limit).all()


def get_branches_count(db: Session, is_active: Optional[bool] = None) -> int:
    """عدد الفروع"""
    query = db.query(Branch)
    if is_active is not None:
        query = query.filter(Branch.is_active == is_active)
    return query.count()


# 
# إنشاء
# 

def create_branch(db: Session, branch: BranchCreate):
    """إنشاء فرع جديد"""
    # التحقق من كود الفرع
    existing_code = db.query(Branch).filter(Branch.code == branch.code).first()
    if existing_code:
        return {
            "error": "code_duplicate",
            "message": f"كود الفرع '{branch.code}' مستخدم مسبقا للفرع: {existing_code.name}",
        }

    # التحقق من الاسم
    existing_name = db.query(Branch).filter(Branch.name == branch.name).first()
    if existing_name:
        return {
            "error": "name_duplicate",
            "message": f"اسم الفرع '{branch.name}' موجود مسبقا",
        }

    db_branch = Branch(
        code=branch.code,
        name=branch.name,
        name_en=branch.name_en,
        city_id=branch.city_id,
        address=branch.address,
        address_en=branch.address_en,
        phone=branch.phone,
        email=branch.email,
        manager_name=branch.manager_name,
        manager_phone=branch.manager_phone,
        opened_at=branch.opened_at,
        is_active=branch.is_active if branch.is_active is not None else True,
        notes=branch.notes,
    )
    db.add(db_branch)
    db.commit()
    db.refresh(db_branch)
    return db_branch


# 
# تعديل
# 

def update_branch(db: Session, branch_id: int, branch: BranchUpdate):
    """تعديل فرع"""
    db_branch = get_branch(db, branch_id)
    if not db_branch:
        return None

    # تحديث الحقول المرسلة فقط
    update_data = branch.model_dump(exclude_unset=True)

    # التحقق من الاسم إذا تم تغييره
    if "name" in update_data and update_data["name"] != db_branch.name:
        existing = db.query(Branch).filter(
            Branch.name == update_data["name"],
            Branch.id != branch_id,
        ).first()
        if existing:
            return {
                "error": "name_duplicate",
                "message": f"اسم الفرع '{update_data['name']}' موجود مسبقا",
            }

    for key, value in update_data.items():
        setattr(db_branch, key, value)

    db.commit()
    db.refresh(db_branch)
    return db_branch


# 
# حذف
# 

def delete_branch(db: Session, branch_id: int):
    """حذف منطقي  تعطيل الفرع"""
    db_branch = get_branch(db, branch_id)
    if not db_branch:
        return None

    # التحقق: هل هناك حجوزات نشطة في هذا الفرع
    from app.models.bookings_models import Booking, BookingStatus
    active_bookings = db.query(Booking).filter(
        Booking.branch_id == branch_id,
        Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
    ).count()

    if active_bookings > 0:
        return {
            "error": "has_active_bookings",
            "message": f"لا يمكن حذف الفرع  يوجد {active_bookings} حجز نشط",
            "active_bookings": active_bookings,
        }

    db_branch.is_active = False
    db.commit()
    db.refresh(db_branch)
    return db_branch


def hard_delete_branch(db: Session, branch_id: int):
    """حذف فعلي  يستخدم فقط للمدراء العامين بحذر"""
    db_branch = get_branch(db, branch_id)
    if db_branch:
        db.delete(db_branch)
        db.commit()
    return db_branch


# 
# إحصائيات
# 

def get_branch_stats(db: Session, branch_id: int) -> dict:
    """إحصائيات الفرع"""
    from app.models.bookings_models import Booking, BookingStatus
    from app.models.employees_models import Employee
    from sqlalchemy import func

    branch = get_branch(db, branch_id)
    if not branch:
        return {}

    total_bookings = db.query(Booking).filter(Booking.branch_id == branch_id).count()
    confirmed_bookings = db.query(Booking).filter(
        Booking.branch_id == branch_id,
        Booking.status == BookingStatus.CONFIRMED,
    ).count()
    pending_bookings = db.query(Booking).filter(
        Booking.branch_id == branch_id,
        Booking.status == BookingStatus.PENDING,
    ).count()

    total_revenue = db.query(func.sum(Booking.total_price)).filter(
        Booking.branch_id == branch_id,
        Booking.status == BookingStatus.CONFIRMED,
    ).scalar() or 0

    total_employees = db.query(Employee).filter(
        Employee.branch_id == branch_id,
        Employee.is_active == True,
    ).count()

    return {
        "branch_id": branch_id,
        "branch_name": branch.name,
        "total_bookings": total_bookings,
        "confirmed_bookings": confirmed_bookings,
        "pending_bookings": pending_bookings,
        "total_revenue": float(total_revenue),
        "total_employees": total_employees,
    }
