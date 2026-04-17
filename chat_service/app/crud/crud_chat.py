from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models.chat_model import ChatMessage
from datetime import datetime, timedelta

def create_message(db: Session, user_id: int, sender_name: str, message: str, receiver_id: int = None):
    new_msg = ChatMessage(
        user_id=user_id,
        receiver_id=receiver_id,
        sender_name=sender_name,
        message=message
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    return new_msg

def get_global_history(db: Session, limit: int = 50):
    # Lấy tin nhắn không có người nhận (Chat hệ thống)
    return db.query(ChatMessage).filter(ChatMessage.receiver_id == None)\
             .order_by(ChatMessage.created_at.asc()).limit(limit).all()

def get_private_history(db: Session, user1_id: int, user2_id: int, limit: int = 50):
    # Lấy tin nhắn qua lại giữa 2 người
    return db.query(ChatMessage).filter(
        or_(
            and_(ChatMessage.user_id == user1_id, ChatMessage.receiver_id == user2_id),
            and_(ChatMessage.user_id == user2_id, ChatMessage.receiver_id == user1_id)
        )
    ).order_by(ChatMessage.created_at.asc()).limit(limit).all()

# ==========================================
# 4. CRONJOB: XÓA TIN NHẮN CŨ (Dọn Rác)
# ==========================================
def delete_old_messages(db: Session, days: int = 30):
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    deleted_count = db.query(ChatMessage).filter(ChatMessage.created_at < cutoff_date).delete()
    db.commit()
    return deleted_count