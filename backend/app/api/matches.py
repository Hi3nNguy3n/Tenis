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
    category_id: int = Query(None),
    db: Session = Depends(get_db)
):
    match_records = crud_match.get_list_matches(db, tournament_id=tournament_id, category_id=category_id)
    
    results = []
    for m, t, c, cat in match_records:
        p1_name = "Chưa xác định"
        p2_name = "Chưa xác định"
        p1_partner_name = None
        p2_partner_name = None
        p1_avatar = None
        p2_avatar = None
        
        # --- LOGIC TÌM TÊN VĐV ---
        if m.tournament_id: 
            reg_a = db.query(Registration).filter(Registration.id == m.side_a_registration_id).first() if m.side_a_registration_id else None
            if reg_a:
                user_a = db.query(User).join(Player).filter(Player.id == reg_a.player_id).first()
                if user_a: 
                    p1_name = user_a.full_name
                    p1_avatar = user_a.avatar_url
                p1_partner_name = reg_a.partner_name
                        
            reg_b = db.query(Registration).filter(Registration.id == m.side_b_registration_id).first() if m.side_b_registration_id else None
            if reg_b:
                user_b = db.query(User).join(Player).filter(Player.id == reg_b.player_id).first()
                if user_b: 
                    p2_name = user_b.full_name
                    p2_avatar = user_b.avatar_url
                p2_partner_name = reg_b.partner_name
        else: 
            # 2. Trận GIAO HỮU
            player_a = db.query(Player).filter(Player.id == m.player_a_id).first() if m.player_a_id else None
            if player_a:
                user_a = db.query(User).filter(User.id == player_a.user_id).first()
                if user_a: 
                    p1_name = user_a.full_name
                    p1_avatar = user_a.avatar_url
                    
            player_b = db.query(Player).filter(Player.id == m.player_b_id).first() if m.player_b_id else None
            if player_b:
                user_b = db.query(User).filter(User.id == player_b.user_id).first()
                if user_b: 
                    p2_name = user_b.full_name
                    p2_avatar = user_b.avatar_url

            # Giao hữu đấu đôi:
            if m.player_a2_id:
                player_a2 = db.query(Player).filter(Player.id == m.player_a2_id).first()
                if player_a2:
                    user_a2 = db.query(User).filter(User.id == player_a2.user_id).first()
                    if user_a2:
                        p1_partner_name = user_a2.full_name
            if m.player_b2_id:
                player_b2 = db.query(Player).filter(Player.id == m.player_b2_id).first()
                if player_b2:
                    user_b2 = db.query(User).filter(User.id == player_b2.user_id).first()
                    if user_b2:
                        p2_partner_name = user_b2.full_name

        display_name = t.name if t else (m.round_code if m.round_code else ("Trận Giao Hữu 2vs2" if m.match_type == "doubles" else "Trận Giao Hữu 1vs1"))

        results.append({
            "id": m.id,
            "tournament": display_name,
            "category_name": cat.name if cat else "N/A",
            "p1_name": p1_name,
            "p2_name": p2_name,
            "p1_avatar": p1_avatar,
            "p2_avatar": p2_avatar,
            "p1_partner_name": p1_partner_name,
            "p2_partner_name": p2_partner_name,
            "court": c.court_name if c else "Chưa gán sân",
            "court_id": m.court_id,
            "tournament_start_date": t.start_date.isoformat() if t and t.start_date else None,
            "tournament_end_date": t.end_date.isoformat() if t and t.end_date else None,
            "score_summary": m.score_summary,
            "score_a": m.set1_a,
            "score_b": m.set1_b,
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
            "referee_id": m.referee_id,
            "referee_name": m.referee_name,
            "referee_phone": m.referee_phone,
            "video_url": m.video_url,
            "image_url": m.image_url,
            
            "match_type": m.match_type or "singles",
            "player_a_id": m.player_a_id,
            "player_b_id": m.player_b_id,
            "player_a2_id": m.player_a2_id,
            "player_b2_id": m.player_b2_id
        })
    return results

# 1. TẠO KHUÔN DỮ LIỆU (SCHEMA)
class MatchCreate(BaseModel):
    tournament_id: Optional[int] = None # <--- Chuyển thành Optional
    match_name: Optional[str] = "Giao hữu"
    side_a_id: int 
    side_b_id: int
    side_a2_id: Optional[int] = None
    side_b2_id: Optional[int] = None
    match_type: Optional[str] = "singles" # singles hoặc doubles
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

@router.delete("/{match_id}")
def delete_match(
    match_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    try:
        crud_match.cancel_match(db, match_id)
        return {"message": "Đã hủy trận đấu thành công!"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))