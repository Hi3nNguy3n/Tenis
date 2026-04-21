# backend/app/api/matches.py
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.crud import crud_match # Import CRUD mới tạo

from pydantic import BaseModel
from datetime import date, time
from app.api.deps import get_current_admin
from app.models.models import User, Registration, Player
router = APIRouter()

@router.get("/")
def list_matches(
    tournament_id: int = Query(None),
    db: Session = Depends(get_db)
):
    match_records = crud_match.get_list_matches(db, tournament_id=tournament_id)
    
    results = []
    for m, t, c in match_records:
        p1_name = "Chưa xác định"
        p2_name = "Chưa xác định"
        
        # --- LOGIC TÌM TÊN VĐV (Đã fix cầu nối an toàn qua bảng Player) ---
        if m.tournament_id: 
            # 1. Trận đấu GIẢI (Tìm qua Registration -> Player -> User)
            if m.side_a_registration_id:
                reg_a = db.query(Registration).filter(Registration.id == m.side_a_registration_id).first()
                if reg_a and reg_a.player_id:
                    player_a = db.query(Player).filter(Player.id == reg_a.player_id).first()
                    if player_a and player_a.user_id:
                        user_a = db.query(User).filter(User.id == player_a.user_id).first()
                        if user_a: p1_name = user_a.full_name
                        
            if m.side_b_registration_id:
                reg_b = db.query(Registration).filter(Registration.id == m.side_b_registration_id).first()
                if reg_b and reg_b.player_id:
                    player_b = db.query(Player).filter(Player.id == reg_b.player_id).first()
                    if player_b and player_b.user_id:
                        user_b = db.query(User).filter(User.id == player_b.user_id).first()
                        if user_b: p2_name = user_b.full_name
        else: 
            # 2. Trận GIAO HỮU (Tìm qua Player_id -> User)
            if m.player_a_id:
                player_a = db.query(Player).filter(Player.id == m.player_a_id).first()
                if player_a:
                    user_a = db.query(User).filter(User.id == player_a.user_id).first()
                    if user_a: p1_name = user_a.full_name
                    
            if m.player_b_id:
                player_b = db.query(Player).filter(Player.id == m.player_b_id).first()
                if player_b:
                    user_b = db.query(User).filter(User.id == player_b.user_id).first()
                    if user_b: p2_name = user_b.full_name

        # --- BƯỚC XỬ LÝ TÊN HIỂN THỊ CỦA GIẢI / TRẬN ---
        # Nếu có giải -> lấy tên giải. Nếu Giao hữu -> lấy round_code (tên custom Admin đặt)
        display_name = t.name if t else (m.round_code if m.round_code else "Trận Giao Hữu 1vs1")

        # Đóng gói dữ liệu "All-in-one" (Dùng chung cho cả MatchesView và ScheduleView)
        results.append({
            "id": m.id,
            "tournament": display_name,
            "court": c.court_name if c else "Chưa gán sân",
            "court_id": m.court_id,
            "date": m.match_date.isoformat() if m.match_date else None,
            
            # Phục vụ trang Điều phối (Match Control) - Dùng ISO format
            "start_time": m.start_time.isoformat() if m.start_time else None,
            
            # Phục vụ trang Lịch trình (Schedule) - Dùng string HH:MM
            "start": m.start_time.strftime("%H:%M") if m.start_time else "--:--",
            "end": m.end_time.strftime("%H:%M") if m.end_time else "--:--",
            
            "status": m.status,
            "round_code": m.round_code,
            "match_no": m.match_no,
            "winner_side": m.winner_side,
            "p1_name": p1_name,
            "p2_name": p2_name
        })
    return results

# 1. TẠO KHUÔN DỮ LIỆU (SCHEMA)
class MatchCreate(BaseModel):
    tournament_id: Optional[int] = None # <--- Chuyển thành Optional
    match_name: Optional[str] = "Giao hữu 1vs1"
    side_a_id: int 
    side_b_id: int
    court_id: Optional[int] = None
    match_date: Optional[date] = None
    start_time: Optional[time] = None
# 2. API TẠO TRẬN ĐẤU (CHỈ ADMIN)
@router.post("/")
def create_match(
    match_in: MatchCreate, 
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin) # Bảo mật: Chỉ Admin được gọi
):
    try:
        new_match = crud_match.create_manual_match(db, match_in)
        return {
            "message": "Tạo trận đấu thủ công thành công!", 
            "match_id": new_match.id
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))