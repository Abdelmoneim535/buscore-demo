from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.database import get_db
from app.routers.auth_routes import get_current_admin
from app.crud import branches_crud
from app.schemas.branches_schemas import (
    BranchCreate,
    BranchUpdate,
    BranchResponse,
    BranchSimple,
)

router = APIRouter(prefix="/branches", tags=["الفروع"])


# 
# قراءة (عام)
# 

@router.get("/", response_model=List[BranchResponse])
def get_branches(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """قائمة الفروع"""
    return branches_crud.get_branches(db, skip=skip, limit=limit, is_active=is_active)


@router.get("/simple", response_model=List[BranchSimple])
def get_branches_simple(
    is_active: bool = True,
    db: Session = Depends(get_db),
):
    """قائمة الفروع (معلومات مختصرة)  للاستخدام في القوائم المنسدلة"""
    return branches_crud.get_branches(db, is_active=is_active)


@router.get("/count")
def get_branches_count(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """عدد الفروع"""
    return {"count": branches_crud.get_branches_count(db, is_active=is_active)}


@router.get("/code/{code}", response_model=BranchResponse)
def get_branch_by_code(code: str, db: Session = Depends(get_db)):
    """جلب فرع بالكود (BR-001)"""
    branch = branches_crud.get_branch_by_code(db, code)
    if not branch:
        raise HTTPException(status_code=404, detail="الفرع غير موجود")
    return branch


@router.get("/{branch_id}", response_model=BranchResponse)
def get_branch(branch_id: int, db: Session = Depends(get_db)):
    """جلب فرع بالمعرف"""
    branch = branches_crud.get_branch(db, branch_id)
    if not branch:
        raise HTTPException(status_code=404, detail="الفرع غير موجود")
    return branch


@router.get("/{branch_id}/stats")
def get_branch_stats(branch_id: int, db: Session = Depends(get_db)):
    """إحصائيات الفرع"""
    stats = branches_crud.get_branch_stats(db, branch_id)
    if not stats:
        raise HTTPException(status_code=404, detail="الفرع غير موجود")
    return stats


# 
# إنشاء / تعديل / حذف (محمي)
# 

@router.post("/", response_model=BranchResponse, dependencies=[Depends(get_current_admin)])
def create_branch(branch: BranchCreate, db: Session = Depends(get_db)):
    """إنشاء فرع جديد"""
    result = branches_crud.create_branch(db, branch)
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.put("/{branch_id}", response_model=BranchResponse, dependencies=[Depends(get_current_admin)])
def update_branch(branch_id: int, branch: BranchUpdate, db: Session = Depends(get_db)):
    """تعديل فرع"""
    result = branches_crud.update_branch(db, branch_id, branch)
    if result is None:
        raise HTTPException(status_code=404, detail="الفرع غير موجود")
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.delete("/{branch_id}", dependencies=[Depends(get_current_admin)])
def delete_branch(branch_id: int, db: Session = Depends(get_db)):
    """حذف منطقي  تعطيل الفرع"""
    result = branches_crud.delete_branch(db, branch_id)
    if result is None:
        raise HTTPException(status_code=404, detail="الفرع غير موجود")
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
    return {"message": f"تم تعطيل الفرع '{result.name}' بنجاح"}


@router.delete("/{branch_id}/hard", dependencies=[Depends(get_current_admin)])
def hard_delete_branch(branch_id: int, db: Session = Depends(get_db)):
    """حذف فعلي  للمدير العام فقط"""
    result = branches_crud.hard_delete_branch(db, branch_id)
    if not result:
        raise HTTPException(status_code=404, detail="الفرع غير موجود")
    return {"message": f"تم حذف الفرع '{result.name}' نهائيًا"}
