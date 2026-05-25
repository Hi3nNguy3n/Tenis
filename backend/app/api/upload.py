from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import cloudinary.uploader

from app.api.deps import get_current_admin

router = APIRouter()

MAX_IMAGE_SIZE_MB = 10
MAX_VIDEO_SIZE_MB = 80
MAX_VIDEO_DURATION_SECONDS = 60
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/svg+xml"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime", "video/x-msvideo"}


def _file_size_bytes(file: UploadFile) -> int:
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    return size


@router.post("/image")
def upload_image(
    file: UploadFile = File(...),
    current_user=Depends(get_current_admin)
):
    content_type = (file.content_type or "").lower()
    is_image = content_type in ALLOWED_IMAGE_TYPES
    is_video = content_type in ALLOWED_VIDEO_TYPES

    if not is_image and not is_video:
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ upload ảnh hoặc video MP4/WebM/MOV/AVI.")

    size_bytes = _file_size_bytes(file)
    max_bytes = (MAX_VIDEO_SIZE_MB if is_video else MAX_IMAGE_SIZE_MB) * 1024 * 1024
    if size_bytes > max_bytes:
        limit = MAX_VIDEO_SIZE_MB if is_video else MAX_IMAGE_SIZE_MB
        raise HTTPException(status_code=413, detail=f"File vượt quá giới hạn {limit}MB.")

    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder="tennis_app/news",
            resource_type="video" if is_video else "image"
        )

        duration = float(result.get("duration") or 0)
        if is_video and duration > MAX_VIDEO_DURATION_SECONDS:
            public_id = result.get("public_id")
            if public_id:
                cloudinary.uploader.destroy(public_id, resource_type="video")
            raise HTTPException(
                status_code=400,
                detail=f"Video phải ngắn hơn hoặc bằng {MAX_VIDEO_DURATION_SECONDS} giây."
            )

        return {"url": result.get("secure_url")}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống upload: {str(e)}")
