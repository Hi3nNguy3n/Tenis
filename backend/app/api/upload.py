# backend/app/api/upload.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import cloudinary
import cloudinary.uploader
from app.api.deps import get_current_admin # Chỉ admin mới được dùng cổng này cho News

router = APIRouter()

@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    current_user = Depends(get_current_admin)
):
    try:
        # Tải ảnh lên Cloudinary vào thư mục riêng cho News
        result = cloudinary.uploader.upload(
            file.file,
            folder="tennis_app/news",
            resource_type="image"
        )
        # Trả về URL để Frontend lưu vào bảng Posts
        return {"url": result.get("secure_url")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống upload: {str(e)}")