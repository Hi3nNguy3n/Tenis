# backend/app/db/seed.py
from sqlalchemy.orm import Session
from app.models.models import Role, User, Player
from app.core.security import get_password_hash
from app.db.database import SessionLocal

def seed_data():
    db = SessionLocal()
    try:
        # 1. Tạo các Role cơ bản
        roles_data = [
            {"key": "admin", "name": "Quản trị viên", "scope": "system"},
            {"key": "user", "name": "Người dùng/VĐV", "scope": "app"}
        ]

        for r_data in roles_data:
            role = db.query(Role).filter(Role.role_key == r_data["key"]).first()
            if not role:
                new_role = Role(
                    role_key=r_data["key"],
                    role_name=r_data["name"],
                    scope=r_data["scope"]
                )
                db.add(new_role)
                print(f"✅ Đã tạo Role: {r_data['key']}")
        
        db.commit() # Lưu Role trước để lấy ID cho User

        # 2. Tạo tài khoản Admin mặc định
        admin_email = "admin@saigontennistour.com"
        admin_user = db.query(User).filter(User.email == admin_email).first()
        
        if not admin_user:
            admin_role = db.query(Role).filter(Role.role_key == "admin").first()
            
            new_admin = User(
                email=admin_email,
                password_hash=get_password_hash("admin@123"), # Mật khẩu mặc định
                full_name="System Admin",
                account_type="admin",
                role_id=admin_role.id,
                is_verified=True,
                is_active=True
            )
            db.add(new_admin)
            db.flush() # Lấy ID của admin vừa tạo

            # Tạo kèm profile Player cho admin (nếu cần tham gia test giải)
            new_player = Player(
                user_id=new_admin.id,
                elo_points=1200, # Admin cho điểm cao chút
                matches_played=0
            )
            db.add(new_player)
            
            db.commit()
            print(f"🚀 Đã tạo tài khoản Admin mặc định: {admin_email} / Admin@123")
        else:
            print("ℹ️ Tài khoản Admin đã tồn tại, bỏ qua bước tạo mới.")

    except Exception as e:
        print(f"❌ Lỗi khi tạo Seed Data: {e}")
        db.rollback()
    finally:
        db.close()