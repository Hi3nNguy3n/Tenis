# backend/app/db/database.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import OperationalError
import os
import logging
from dotenv import load_dotenv

# Load các biến từ file .env
load_dotenv()

logger = logging.getLogger(__name__)

# Đọc từ .env, nếu không có thì lấy cái Local làm dự phòng
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://admin:secret@127.0.0.1:5432/saigon_tennis_db"
)

# Khôi phục lại create_engine nguyên bản, không dùng connect_args phức tạp
engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)

# Tạo Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class cho các models
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        # Kiem tra nhanh ket noi
        db.execute(text("SELECT 1"))
        yield db
    except OperationalError as e:
        logger.error(f"DATABASE ERROR: Khong the ket noi co so du lieu. {e}")
        raise e
    except Exception as e:
        logger.error(f"LOI KHONG XAC DINH: {e}")
        raise e
    finally:
        db.close()