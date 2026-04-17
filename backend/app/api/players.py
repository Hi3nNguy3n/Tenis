# backend/app/api/players.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
import cloudinary.uploader
from typing import Optional

from app.db.database import get_db
from app.api.deps import get_current_user
from app.models.models import User
from app.schemas.player_schemas import PlayerUpdate
from app.core.audit import audit_log
from app.crud import crud_player # Import tầng CRUD mới cấu trúc

router = APIRouter()

@router.get("/me")
def read_user_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    player_info = crud_player.get_player_by_user_id(db, current_user.id)
    return {
        "user": current_user,
        "player_profile": player_info
    }

@router.put("/me")
@audit_log(module="PLAYER", action="UPDATE", event_name="Cá nhân tự cập nhật hồ sơ")
def update_profile(
    update_data: PlayerUpdate, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    updated_user, _ = crud_player.update_player_profile(db, current_user, update_data)
    return {"message": "Cập nhật thông tin thành công", "user": updated_user}

@router.post("/me/avatar")
@audit_log(module="PLAYER", action="UPDATE", event_name="Cá nhân cập nhật ảnh đại diện")
def upload_avatar(
    file: UploadFile = File(...), 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    try:
        result = cloudinary.uploader.upload(file.file, folder="saigon_tennis/avatars")
        avatar_url = result.get("secure_url")
        
        crud_player.update_user_avatar(db, current_user, avatar_url)
        return {"avatar_url": avatar_url, "message": "Cập nhật ảnh đại diện thành công"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi upload ảnh: {str(e)}")

@router.get("/list")
def list_players(
    search: Optional[str] = Query(None),
    skill: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    players_data = crud_player.get_players_list(db, search, skill, status)
    
    results = []
    for p, u in players_data:
        results.append({
            "id": p.id,
            "user": u,
            "player_profile": p
        })
    return results

@router.put("/{player_id}")
@audit_log(module="PLAYER", action="UPDATE", event_name="Admin cập nhật hồ sơ VĐV")
def admin_update_player(
    player_id: int,
    data: PlayerUpdate, 
    db: Session = Depends(get_db)
):
    player = crud_player.admin_update_player_data(db, player_id, data)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return {"message": "Player updated"}

@router.get("/rankings")
def get_global_rankings(
    category: Optional[str] = Query(None, description="Lọc theo nội dung (Singles/Doubles)"),
    province: Optional[str] = Query(None, description="Lọc theo tỉnh thành"),
    db: Session = Depends(get_db)
):
    players_data = crud_player.get_player_rankings(db, category, province)

    results = []
    for rank, (p, u) in enumerate(players_data, start=1):
        win_rate = 0
        if p.matches_played > 0:
            win_rate = round((p.wins / p.matches_played) * 100, 1)

        results.append({
            "rank": rank,
            "player_id": p.id,
            "full_name": u.full_name,
            "avatar_url": u.avatar_url,
            "elo_points": p.elo_points,
            "wins": p.wins,
            "losses": p.losses,
            "matches_played": p.matches_played,
            "win_rate": win_rate,
            "skill_level": p.skill_level or "Unranked",
            "province": u.province,
            "category": p.preferred_category
        })
    return results

@router.get("/me/history")
def get_my_match_history(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    player = crud_player.get_player_by_user_id(db, current_user.id)
    if not player:
        return []

    reg_ids = crud_player.get_player_registrations(db, player.id)
    matches_data = crud_player.get_matches_by_registrations(db, reg_ids)

    results = []
    for m, t, c in matches_data:
        is_side_a = m.side_a_registration_id in reg_ids
        opponent_reg_id = m.side_b_registration_id if is_side_a else m.side_a_registration_id
        
        opponent_name = "Đang chờ đối thủ"
        if opponent_reg_id:
            opp_user = crud_player.get_opponent_user_by_reg_id(db, opponent_reg_id)
            opponent_name = opp_user.full_name if opp_user else "VĐV"

        result_status = "Đang chờ"
        if m.status == "completed":
            my_side = "side_a" if is_side_a else "side_b"
            result_status = "THẮNG" if m.winner_side == my_side else "THUA"

        results.append({
            "id": m.id,
            "tournament_name": t.name,
            "round": m.round_code,
            "opponent": opponent_name,
            "score": m.result_note or "- / -",
            "status": result_status,
            "court": c.court_name if c else "N/A",
            "time": m.start_time.strftime("%d/%m/%Y %H:%M") if m.start_time else "TBD"
        })
    return results