# backend/app/api/tournaments.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.api.deps import get_current_user, get_current_admin
from app.models.models import User, Tournament
from app.crud import crud_tournament
from app.schemas import tournament_schemas

router = APIRouter()

# 1. TẠO GIẢI ĐẤU (CHỈ ADMIN)
@router.post("/", response_model=tournament_schemas.TournamentResponse)
def create_tournament(
    tournament: tournament_schemas.TournamentCreate,
    current_admin: User = Depends(get_current_admin), # Chốt chặn Admin nằm ở đây
    db: Session = Depends(get_db)
):
    return crud_tournament.create_tournament(db=db, tournament=tournament)

# 2. XEM DANH SÁCH GIẢI ĐẤU (PUBLIC - AI CŨNG XEM ĐƯỢC)
@router.get("/", response_model=List[tournament_schemas.TournamentResponse])
def read_tournaments(
    skip: int = Query(0, description="Bỏ qua bao nhiêu bản ghi đầu"),
    limit: int = Query(10, description="Lấy tối đa bao nhiêu bản ghi"),
    status: str = Query(None, description="Lọc theo trạng thái: draft, open, ongoing, finished"),
    db: Session = Depends(get_db)
):
    return crud_tournament.get_tournaments(db, skip=skip, limit=limit, status=status)

# 3. XEM CHI TIẾT 1 GIẢI ĐẤU (PUBLIC)
@router.get("/{tournament_id}", response_model=tournament_schemas.TournamentResponse)
def read_tournament(tournament_id: int, db: Session = Depends(get_db)):
    db_tournament = crud_tournament.get_tournament(db, tournament_id=tournament_id)
    if db_tournament is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy giải đấu")
    return db_tournament