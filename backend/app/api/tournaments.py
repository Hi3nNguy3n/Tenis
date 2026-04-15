# backend/app/api/tournaments.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from pydantic import BaseModel

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.models.models import User
from app.crud import crud_tournament
from app.schemas import tournament_schemas
from app.core.audit import audit_log

router = APIRouter()

# 1. TẠO GIẢI ĐẤU (CHỈ ADMIN)
@router.post("/", response_model=tournament_schemas.TournamentResponse)
@audit_log(module="TOURNAMENT", action="CREATE", event_name="Khởi tạo giải đấu mới")
def create_tournament(
    tournament: tournament_schemas.TournamentCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    return crud_tournament.create_tournament(db=db, tournament=tournament)

# 2. XEM DANH SÁCH GIẢI ĐẤU (PUBLIC)
@router.get("/", response_model=List[tournament_schemas.TournamentResponse])
def read_tournaments(
    skip: int = Query(0, description="Bỏ qua bao nhiêu bản ghi đầu"),
    limit: int = Query(10, description="Lấy tối đa bao nhiêu bản ghi"),
    status: str = Query(None, description="Lọc theo trạng thái: draft, open, ongoing, finished"),
    db: Session = Depends(get_db)
):
    return crud_tournament.get_tournaments_with_counts(db, skip=skip, limit=limit, status=status)

# 3. XEM CHI TIẾT 1 GIẢI ĐẤU (PUBLIC)
@router.get("/{tournament_id}", response_model=tournament_schemas.TournamentResponse)
def read_tournament(tournament_id: int, db: Session = Depends(get_db)):
    return crud_tournament.get_tournament_with_count(db, tournament_id=tournament_id)

# 4. THỐNG KÊ TỔNG QUAN (ADMIN ONLY)
@router.get("/summary/stats", dependencies=[Depends(get_current_admin)])
def read_tournament_stats(db: Session = Depends(get_db)):
    return crud_tournament.get_system_stats(db)

# 5. CẬP NHẬT GIẢI ĐẤU (CHỈ ADMIN)
@router.put("/{tournament_id}", response_model=tournament_schemas.TournamentResponse)
@audit_log(module="TOURNAMENT", action="UPDATE", event_name="Cập nhật cấu hình giải đấu")
def update_tournament(
    tournament_id: int,
    tournament_in: tournament_schemas.TournamentCreate, 
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    return crud_tournament.update_tournament_info(db, tournament_id, tournament_in, current_admin.id)

# 6. GENERATE DRAW (ADMIN ONLY)
@router.post("/{tournament_id}/generate-draw", dependencies=[Depends(get_current_admin)])
@audit_log(module="TOURNAMENT", action="UPDATE", event_name="Tự động sinh sơ đồ nhánh đấu (Bracket)")
def generate_tournament_draw(tournament_id: int, db: Session = Depends(get_db)):
    return crud_tournament.generate_knockout_draw(db, tournament_id=tournament_id)

# 7. XEM DANH SÁCH TRẬN ĐẤU (PUBLIC)
@router.get("/{tournament_id}/matches")
def read_tournament_matches(tournament_id: int, db: Session = Depends(get_db)):
    return crud_tournament.get_tournament_matches_detail(db, tournament_id=tournament_id)

class MatchScheduleUpdate(BaseModel):
    court_id: int
    start_time: datetime

# 8. GÁN LỊCH THI ĐẤU (ADMIN ONLY)
@router.post("/matches/{match_id}/schedule", dependencies=[Depends(get_current_admin)])
@audit_log(module="MATCH", action="UPDATE", event_name="Gán lịch và phân sân thi đấu")
def schedule_match(match_id: int, payload: MatchScheduleUpdate, db: Session = Depends(get_db)):
    return crud_tournament.schedule_match_db(db, match_id, payload)

# 9. LẤY TẤT CẢ TRẬN ĐẤU (ADMIN ONLY)
@router.get("/matches/all", dependencies=[Depends(get_current_admin)])
def read_all_matches(db: Session = Depends(get_db)):
    return crud_tournament.get_all_matches_detail(db)

class MatchScoreUpdate(BaseModel):
    score: str        
    winner_side: str  

# 10. CẬP NHẬT TỶ SỐ, THĂNG HẠNG & TÍNH ĐIỂM ELO
@router.post("/matches/{match_id}/score", dependencies=[Depends(get_current_admin)])
@audit_log(module="MATCH", action="UPDATE", event_name="Cập nhật tỷ số trận đấu")
def update_match_score(match_id: int, payload: MatchScoreUpdate, db: Session = Depends(get_db)):
    return crud_tournament.calculate_elo_and_update_match(db, match_id, payload)

# 11. XEM BRACKET CÔNG KHAI
@router.get("/{tournament_id}/public-bracket")
def get_public_bracket(tournament_id: int, db: Session = Depends(get_db)):
    return crud_tournament.get_public_bracket_detail(db, tournament_id=tournament_id)