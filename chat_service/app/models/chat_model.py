from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.db.database import Base

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True) # ID người gửi
    receiver_id = Column(Integer, index=True, nullable=True) # ID người nhận (null = chat hệ thống)
    sender_name = Column(String)
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)