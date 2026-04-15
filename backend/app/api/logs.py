# backend/app/api/logs.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.deps import get_current_admin
from app.models.models import User
from app.crud import crud_logs # Import CRUD mới tạo

router = APIRouter()

@router.get("/activity")
def get_activity_logs(
    skip: int = 0, 
    limit: int = 50,
    module: str = Query(None),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    # ĐÃ REFACTOR: Đẩy câu lệnh query phức tạp xuống tầng CRUD
    logs = crud_logs.get_activity_logs(db, skip=skip, limit=limit, module=module)
    
    # Giữ nguyên logic format dữ liệu trả về cho Frontend
    results = []
    for log, user_name in logs:
        results.append({
            "id": log.id,
            "user_name": user_name or "System",
            "module_name": log.module_name,
            "action_type": log.action_type,
            "event_name": log.event_name,
            "ip_address": log.ip_address,
            "old_data": log.old_data_json,
            "new_data": log.new_data_json,
            "created_at": log.created_at
        })
    return results