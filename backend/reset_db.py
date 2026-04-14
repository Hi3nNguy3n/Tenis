# backend/reset_db.py
from app.db.database import engine, Base
from app.db.seed import seed_data

# QUAN TRỌNG: Phải import tất cả các models vào đây để Base nhận diện được cấu trúc bảng
from app.models.models import User, Player, AuthOtp, Role

def reset_database():
    print("⚠️  Đang xóa toàn bộ cấu trúc bảng cũ...")
    Base.metadata.drop_all(bind=engine)
    
    print("🔨 Đang khởi tạo lại cấu trúc bảng mới...")
    Base.metadata.create_all(bind=engine)
    
    print("🌱 Đang chạy dữ liệu Seed (Khởi tạo Admin & Roles)...")
    seed_data()
    
    print("✅ RESET DATABASE THÀNH CÔNG!")

if __name__ == "__main__":
    reset_database()