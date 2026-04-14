# backend/app/api/players.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import cloudinary.uploader

from app.db.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, Player
from app.schemas.player_schemas import PlayerUpdate

router = APIRouter()

@router.get("/me")
def read_user_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Lấy thêm thông tin Player kết hợp với User
    player_info = db.query(Player).filter(Player.user_id == current_user.id).first()
    
    return {
        "user": current_user,
        "player_profile": player_info
    }

@router.put("/me")
def update_profile(
    update_data: PlayerUpdate, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # Cập nhật bảng User (Họ tên, SĐT)
    if update_data.full_name:
        current_user.full_name = update_data.full_name
    if update_data.phone:
        current_user.phone = update_data.phone

    # Cập nhật bảng Player (Giới tính, Ngày sinh)
    player = db.query(Player).filter(Player.user_id == current_user.id).first()
    if player:
        if update_data.gender:
            player.gender = update_data.gender
        if update_data.date_of_birth:
            player.date_of_birth = update_data.date_of_birth

    db.commit()
    db.refresh(current_user)
    return {"message": "Cập nhật thông tin thành công", "user": current_user}

@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...), 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # 1. Kiểm tra định dạng file
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File tải lên phải là hình ảnh (jpg, png...)")
    
    # 2. Upload lên Cloudinary
    try:
        # Gắn thêm thư mục 'avatars' để dễ quản lý trên Cloudinary
        result = cloudinary.uploader.upload(
            file.file, 
            folder="saigon_tennis/avatars",
            transformation=[{"width": 500, "height": 500, "crop": "fill"}] # Tự động cắt ảnh vuông
        )
        image_url = result.get("secure_url")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi upload ảnh: {str(e)}")

    # 3. Lưu URL vào Database
    current_user.avatar_url = image_url
    db.commit()
    db.refresh(current_user)

    return {"message": "Cập nhật ảnh đại diện thành công", "avatar_url": image_url}