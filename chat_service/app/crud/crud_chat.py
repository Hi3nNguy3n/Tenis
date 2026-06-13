from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models.chat_model import ChatMessage
from datetime import datetime, timedelta

def create_message(db: Session, user_id: int, sender_name: str, message: str, receiver_id: int = None):
    new_msg = ChatMessage(
        user_id=user_id,
        receiver_id=receiver_id,
        sender_name=sender_name,
        message=message,
        is_read=receiver_id is None,
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    return new_msg

def get_global_history(db: Session, limit: int = 20, skip: int = 0):
    # Lấy tin nhắn không có người nhận (Chat hệ thống)
    messages = db.query(ChatMessage).filter(ChatMessage.receiver_id == None)\
                 .order_by(ChatMessage.created_at.desc())\
                 .offset(skip).limit(limit).all()
    messages.reverse()
    return messages

def get_private_history(db: Session, user1_id: int, user2_id: int, limit: int = 20, skip: int = 0):
    # Lấy tin nhắn qua lại giữa 2 người
    messages = db.query(ChatMessage).filter(
        or_(
            and_(ChatMessage.user_id == user1_id, ChatMessage.receiver_id == user2_id),
            and_(ChatMessage.user_id == user2_id, ChatMessage.receiver_id == user1_id)
        )
    ).order_by(ChatMessage.created_at.desc())\
     .offset(skip).limit(limit).all()
    messages.reverse()
    return messages

def mark_private_messages_as_read(db: Session, reader_id: int, other_user_id: int):
    updated = db.query(ChatMessage).filter(
        ChatMessage.user_id == other_user_id,
        ChatMessage.receiver_id == reader_id,
        ChatMessage.is_read.is_(False),
    ).update(
        {
            ChatMessage.is_read: True,
            ChatMessage.read_at: datetime.utcnow(),
        },
        synchronize_session=False,
    )
    db.commit()
    return updated

def get_private_thread_summaries(db: Session, user_id: int):
    messages = db.query(ChatMessage).filter(
        or_(
            ChatMessage.user_id == user_id,
            ChatMessage.receiver_id == user_id,
        ),
        ChatMessage.receiver_id.isnot(None),
    ).order_by(ChatMessage.created_at.desc()).all()

    summaries = []
    seen = set()
    for msg in messages:
        thread_id = msg.receiver_id if msg.user_id == user_id else msg.user_id
        if thread_id in seen:
            continue
        seen.add(thread_id)
        unread_count = db.query(ChatMessage).filter(
            ChatMessage.user_id == thread_id,
            ChatMessage.receiver_id == user_id,
            ChatMessage.is_read.is_(False),
        ).count()
        summaries.append({
            "id": thread_id,
            "sender_name": msg.sender_name,
            "lastMsg": msg.message,
            "updatedAt": msg.created_at,
            "unreadCount": unread_count,
        })
    return summaries

def delete_private_thread(db: Session, user1_id: int, user2_id: int):
    deleted = db.query(ChatMessage).filter(
        or_(
            and_(ChatMessage.user_id == user1_id, ChatMessage.receiver_id == user2_id),
            and_(ChatMessage.user_id == user2_id, ChatMessage.receiver_id == user1_id)
        )
    ).delete(synchronize_session=False)
    db.commit()
    return deleted

# ==========================================
# 4. CRONJOB: XÓA TIN NHẮN CŨ (Dọn Rác)
# ==========================================
def delete_old_messages(db: Session, days: int = 30):
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    deleted_count = db.query(ChatMessage).filter(ChatMessage.created_at < cutoff_date).delete()
    db.commit()
    return deleted_count
