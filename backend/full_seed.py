from sqlalchemy.orm import Session
from app.models.models import Role, User, Player, Tournament, TournamentCategory
from app.core.security import get_password_hash
from app.db.database import SessionLocal
from datetime import datetime, date, timedelta, UTC

def full_seed():
    db = SessionLocal()
    try:
        # 1. Roles
        roles_data = [
            {"key": "admin", "name": "Quản trị viên", "scope": "system"},
            {"key": "user", "name": "Người dùng/VĐV", "scope": "app"}
        ]
        for r_data in roles_data:
            role = db.query(Role).filter(Role.role_key == r_data["key"]).first()
            if not role:
                db.add(Role(role_key=r_data["key"], role_name=r_data["name"], scope=r_data["scope"]))
        db.commit()

        # 2. Admin
        admin_role = db.query(Role).filter(Role.role_key == "admin").first()
        admin = db.query(User).filter(User.email == "admin@saigontennistours.com").first()
        if not admin:
            admin = User(
                email="admin@saigontennistours.com",
                password_hash=get_password_hash("admin@123"),
                full_name="System Admin",
                account_type="admin",
                role_id=admin_role.id,
                is_verified=True,
                is_active=True
            )
            db.add(admin)
            db.flush()
            db.add(Player(user_id=admin.id, elo_points=1200))
            db.commit()

        # 3. Sample Tournament
        tour = db.query(Tournament).filter(Tournament.slug == "saigontennistours-open-2026").first()
        if not tour:
            tour = Tournament(
                name="Saigontennistours Open 2026",
                slug="saigontennistours-open-2026",
                category_type="Open",
                gender_division="Mixed",
                format_type="Doubles",
                draw_size=32,
                registration_open_at=datetime.now(datetime.UTC),
                registration_close_at=datetime.now(datetime.UTC) + timedelta(days=7),
                start_date=date.today() + timedelta(days=10),
                end_date=date.today() + timedelta(days=12),
                status="open",
                location="Saigontennistours Center",
                surface_type="Hard",
                entry_fee=500000,
                entry_fee_team=1000000
            )
            db.add(tour)
            db.flush()

            # 4. Categories for Tournament
            categories = [
                {"name": "Đôi Nam 1275", "type": "mens_doubles", "pts": 1275},
                {"name": "Đôi Nam Nữ 1200", "type": "mixed_doubles", "pts": 1200},
                {"name": "Đơn Nam Open", "type": "mens_singles", "pts": None}
            ]
            for cat_data in categories:
                db.add(TournamentCategory(
                    tournament_id=tour.id,
                    name=cat_data["name"],
                    category_type=cat_data["type"],
                    max_points=cat_data["pts"],
                    max_participants=32
                ))
            db.commit()
            print("✅ Đã tạo giải đấu mẫu và các nội dung thi đấu.")
        else:
            print("ℹ️ Giải đấu mẫu đã tồn tại.")

    except Exception as e:
        print(f"❌ Lỗi: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    full_seed()
