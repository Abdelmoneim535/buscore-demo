from sqlalchemy.orm import Session
from app.models.positions_models import Position
from app.schemas.positions_schemas import PositionCreate


def get_position(db: Session, position_id: int):
    return db.query(Position).filter(Position.id == position_id).first()


def get_positions(db: Session, skip: int = 0, limit: int = 100, active_only: bool = False):
    query = db.query(Position)
    if active_only:
        query = query.filter(Position.is_active == True)
    return query.order_by(Position.sort_order, Position.id).offset(skip).limit(limit).all()


def get_positions_by_category(db: Session, category: str):
    """جلب الوظائف حسب الفئة: driver, assistant, admin, other"""
    return db.query(Position).filter(
        Position.category == category,
        Position.is_active == True
    ).order_by(Position.sort_order, Position.id).all()


def create_position(db: Session, position: PositionCreate):
    #  التحقق من الاسم
    existing = db.query(Position).filter(Position.name == position.name).first()
    if existing:
        return {"error": "name_duplicate", "message": f"الوظيفة '{position.name}' موجودة مسبقًا"}

    db_pos = Position(
        name=position.name,
        name_en=position.name_en,
        category=position.category,
        icon=position.icon,
        sort_order=position.sort_order or 0,
        is_active=position.is_active,
    )
    db.add(db_pos)
    db.commit()
    db.refresh(db_pos)
    return db_pos


def update_position(db: Session, position_id: int, position: PositionCreate):
    db_pos = get_position(db, position_id)
    if not db_pos:
        return None
    db_pos.name = position.name
    db_pos.name_en = position.name_en
    db_pos.category = position.category
    db_pos.icon = position.icon
    db_pos.sort_order = position.sort_order or 0
    db_pos.is_active = position.is_active
    db.commit()
    db.refresh(db_pos)
    return db_pos


def delete_position(db: Session, position_id: int):
    """
    حذف وظيفة. تحقق أولًا من عدم استخدامها من موظفين.
    """
    from app.models.employees_models import Employee

    db_pos = get_position(db, position_id)
    if not db_pos:
        return None

    # التحقق من الموظفين الذين يستخدمون نفس الوظيفة (اسمها العربي)
    employees_using = db.query(Employee).filter(Employee.position == db_pos.name).count()
    if employees_using > 0:
        return {
            "error": True,
            "message": f"لا يمكن الحذف — {employees_using} موظف يستخدم هذه الوظيفة"
        }

    db.delete(db_pos)
    db.commit()
    return db_pos
