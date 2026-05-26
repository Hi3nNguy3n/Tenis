from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import cloudinary.uploader
import logging

from app.api.deps import get_current_admin

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_IMAGE_SIZE_MB = 10
MAX_VIDEO_SIZE_MB = 80
MAX_VIDEO_DURATION_SECONDS = 60
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/svg+xml"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime", "video/x-msvideo"}
INTERNAL_ERROR_MESSAGE = "Đã xảy ra lỗi hệ thống. Vui lòng liên hệ quản trị viên."


def _file_size_bytes(file: UploadFile) -> int:
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    return size


def _get_upload_kind(file: UploadFile) -> str:
    content_type = (file.content_type or "").lower()
    if content_type in ALLOWED_IMAGE_TYPES:
        return "image"
    if content_type in ALLOWED_VIDEO_TYPES:
        return "video"
    raise HTTPException(status_code=400, detail="Chỉ hỗ trợ upload ảnh hoặc video MP4/WebM/MOV/AVI.")


def _validate_upload_file(file: UploadFile, upload_kind: str) -> None:
    size_bytes = _file_size_bytes(file)
    max_mb = MAX_VIDEO_SIZE_MB if upload_kind == "video" else MAX_IMAGE_SIZE_MB
    if size_bytes > max_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File vượt quá giới hạn {max_mb}MB.")


def _upload_media(file: UploadFile) -> dict:
    upload_kind = _get_upload_kind(file)
    _validate_upload_file(file, upload_kind)

    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder="tennis_app/news",
            resource_type=upload_kind,
        )

        duration = float(result.get("duration") or 0)
        if upload_kind == "video" and duration > MAX_VIDEO_DURATION_SECONDS:
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
    except Exception:
        logger.exception("Media upload failed")
        raise HTTPException(status_code=500, detail=INTERNAL_ERROR_MESSAGE)


@router.post("/image")
def upload_image(
    file: UploadFile = File(...),
    current_user=Depends(get_current_admin),
):
    return _upload_media(file)


@router.post("/media")
def upload_media(
    file: UploadFile = File(...),
    current_user=Depends(get_current_admin),
):
    return _upload_media(file)
