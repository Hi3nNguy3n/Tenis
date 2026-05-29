# backend/app/api/courts.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.api.deps import get_current_admin
from app.crud import crud_court
from app.schemas import court_schemas
from app.models.models import User
from app.core.audit import audit_log

router = APIRouter()

@router.get("", response_model=List[court_schemas.CourtResponse], include_in_schema=False)
@router.get("/", response_model=List[court_schemas.CourtResponse])
def read_courts(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    return crud_court.get_courts(db, search=search, status=status)

@router.post("", response_model=court_schemas.CourtResponse, include_in_schema=False)
@router.post("/", response_model=court_schemas.CourtResponse)
@audit_log(module="COURT", action="CREATE", event_name="Tạo sân thi đấu mới")
def create_court(
    court: court_schemas.CourtCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    return crud_court.create_court(db=db, court=court)

@router.put("/{court_id}", response_model=court_schemas.CourtResponse)
@audit_log(module="COURT", action="UPDATE", event_name="Cập nhật thông tin sân")
def update_court(
    court_id: int,
    court_update: court_schemas.CourtUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    db_court = crud_court.update_court(db, court_id=court_id, court_update=court_update)
    if not db_court:
        raise HTTPException(status_code=404, detail="Court not found")
    return db_court

@router.delete("/{court_id}")
@audit_log(module="COURT", action="DELETE", event_name="Xóa sân thi đấu")
def delete_court(
    court_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    crud_court.delete_court(db, court_id=court_id)
    return {"message": "Court deleted"}
