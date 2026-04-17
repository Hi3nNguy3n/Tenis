# backend/app/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# URL kết nối DB cho môi trường Local (chạy Alembic ở ngoài Docker)
SQLALCHEMY_DATABASE_URL = "postgresql://admin:secret@127.0.0.1:5432/saigon_tennis_db"

# Tạo Engine kết nối
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Tạo Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class cho các models (Bạn đã import cái này trong models.py)
Base = declarative_base()

# Dependency để dùng trong các API route
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()