# backend/app/crud/crud_logs.py
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.models import ActivityLog, User

def get_activity_logs(db: Session, skip: int = 0, limit: int = 50, module: str = None):
    """
    Truy vấn log hệ thống, kết hợp với bảng User để lấy tên người thực hiện.
    """
    query = db.query(ActivityLog, User.full_name).outerjoin(
        User, ActivityLog.user_id == User.id
    )
    
    if module:
        query = query.filter(ActivityLog.module_name == module)
        
    return query.order_by(desc(ActivityLog.created_at)).offset(skip).limit(limit).all()