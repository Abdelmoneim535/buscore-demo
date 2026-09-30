from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.database import get_db
from app.routers.auth_routes import get_current_admin
from app.crud import positions_crud
from app.schemas.positions_schemas import PositionCreate, PositionResponse


router = APIRouter(prefix="/positions", tags=["الوظائف"])


@router.get("/", response_model=List[PositionResponse])
def get_positions(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = Query(False),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    if category:
        return positions_crud.get_positions_by_category(db, category)
    return positions_crud.get_positions(db, skip=skip, limit=limit, active_only=active_only)


@router.post("/", response_model=PositionResponse, dependencies=[Depends(get_current_admin)])
def create_position(position: PositionCreate, db: Session = Depends(get_db)):
    if position.category not in ("driver", "assistant", "admin", "other"):
        raise HTTPException(status_code=400, detail="الفئة غير صحيحة")

    result = positions_crud.create_position(db, position)
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.get("/{position_id}", response_model=PositionResponse)
def get_position(position_id: int, db: Session = Depends(get_db)):
    pos = positions_crud.get_position(db, position_id)
    if not pos:
        raise HTTPException(status_code=404, detail="الوظيفة غير موجودة")
    return pos


@router.put("/{position_id}", response_model=PositionResponse, dependencies=[Depends(get_current_admin)])
def update_position(position_id: int, position: PositionCreate, db: Session = Depends(get_db)):
    updated = positions_crud.update_position(db, position_id, position)
    if not updated:
        raise HTTPException(status_code=404, detail="الوظيفة غير موجودة")
    return updated


@router.delete("/{position_id}", dependencies=[Depends(get_current_admin)])
def delete_position(position_id: int, db: Session = Depends(get_db)):
    result = positions_crud.delete_position(db, position_id)
    if not result:
        raise HTTPException(status_code=404, detail="الوظيفة غير موجودة")
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=400, detail=result["message"])
    return {"message": "تم حذف الوظيفة بنجاح"}
