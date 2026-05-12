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

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.schemas.player_schemas import PlayerPublicResponse

from app.api.deps import get_current_admin
from app.schemas.auth_schemas import RegisterRequest
from app.crud import crud_auth

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

# 1. API Tìm kiếm người chơi
@router.get("/search", response_model=List[PlayerPublicResponse])
def search_players(
    keyword: str = Query(..., min_length=1, description="Tên người cần tìm"),
    db: Session = Depends(get_db)
):
    # CRUD giờ đã trả về dữ liệu chuẩn Dictionary khớp với Schema
    return crud_player.search_players(db, keyword=keyword)

# THÊM ĐOẠN NÀY VÀO TRƯỚC @router.get("/{player_id}")
@router.post("/upload-avatar")
def upload_avatar_to_cloudinary(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    try:
        # Thực hiện upload file ảnh thẳng lên Cloudinary
        result = cloudinary.uploader.upload(file.file)
        # Trả về URL an toàn (https)
        return {"avatar_url": result.get("secure_url")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi tải ảnh lên Cloudinary: {str(e)}")
    
# 2. API Lấy hồ sơ công khai của 1 người
@router.get("/{player_id}", response_model=PlayerPublicResponse)
def get_public_profile(player_id: int, db: Session = Depends(get_db)):
    player_data = crud_player.get_player_by_id(db, player_id=player_id)
    if not player_data:
        raise HTTPException(status_code=404, detail="Không tìm thấy người chơi này")
    return player_data

# THÊM API NÀY VÀO CUỐI FILE PLAYERS.PY
@router.post("/admin-create", dependencies=[Depends(get_current_admin)])
@audit_log(module="PLAYER", action="CREATE", event_name="Admin tạo tài khoản VĐV mới")
def admin_create_player(
    request: RegisterRequest, 
    db: Session = Depends(get_db)
):
    # 1. Kiểm tra xem email đã tồn tại trong DB chưa
    user_exists = crud_auth.get_user_by_email(db, request.email)
    if user_exists:
        raise HTTPException(status_code=400, detail="Email này đã được sử dụng trong hệ thống.")
        
    # 2. Lấy role_id của user bình thường
    role = crud_auth.get_role_by_key(db, "user")
    if not role:
        raise HTTPException(status_code=500, detail="Hệ thống chưa cấu hình Role 'user'.")
    
    # 3. Thực hiện Transaction giống hệt user đăng ký (Nhưng bỏ qua check OTP ở auth.py)
    try:
        user = crud_auth.create_user_and_player_transaction(db, request, role.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi DB: {str(e)}")
    
    return {"message": "Tạo tài khoản VĐV thành công!", "user_id": user.id}