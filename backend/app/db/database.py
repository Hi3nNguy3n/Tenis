# backend/app/db/database.py
from sqlalchemy import create_engine
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

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
    pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
    pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "1800")),
    pool_pre_ping=True,
)

# Tạo Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class cho các models
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    except OperationalError as e:
        logger.error(f"DATABASE ERROR: Khong the ket noi co so du lieu. {e}")
        raise e
    except Exception as e:
        logger.error(f"LOI KHONG XAC DINH: {e}")
        raise e
    finally:
        db.close()
