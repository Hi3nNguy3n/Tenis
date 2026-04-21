# backend/app/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv

# Load các biến từ file .env
load_dotenv()

# Đọc từ .env, nếu không có thì lấy cái Local làm dự phòng
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://admin:secret@127.0.0.1:5432/saigon_tennis_db"
)

# Tạo Engine kết nối
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Tạo Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class cho các models
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()