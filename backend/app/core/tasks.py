# backend/app/core/tasks.py
from apscheduler.schedulers.background import BackgroundScheduler
from app.db.database import SessionLocal
from app.crud.crud_registration import cleanup_expired_registrations
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_cleanup_job():
    """Hàm này sẽ tự mở một luồng DB riêng để dọn dẹp"""
    db = SessionLocal()
    try:
        num_cleaned = cleanup_expired_registrations(db)
        if num_cleaned > 0:
            logger.info(f"🧹 [Auto-Cleanup] Đã tự động nhả {num_cleaned} slot quá hạn 15 phút.")
    except Exception as e:
        logger.error(f"Lỗi khi dọn rác: {e}")
    finally:
        db.close() # Xong việc phải đóng kết nối DB lại

def start_scheduler():
    """Khởi động con Bot"""
    scheduler = BackgroundScheduler()
    # Cấu hình cứ mỗi 1 phút nó sẽ tự động chạy hàm run_cleanup_job
    scheduler.add_job(run_cleanup_job, 'interval', minutes=1)
    scheduler.start()
    logger.info("⚙️ Background Scheduler đã được khởi động! (Quét mỗi 1 phút)")