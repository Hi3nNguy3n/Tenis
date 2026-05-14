
from app.db.database import SessionLocal
from app.models.models import User, Player

db = SessionLocal()
all_players = db.query(Player, User).join(User, Player.user_id == User.id).all()
print(f"Total Players in DB: {len(all_players)}")

active_players = [p for p, u in all_players if u.is_active]
inactive_players = [p for p, u in all_players if not u.is_active]

print(f"Active Players: {len(active_players)}")
print(f"Inactive Players: {len(inactive_players)}")

if inactive_players:
    print("\n--- INACTIVE PLAYERS ---")
    for p, u in all_players:
        if not u.is_active:
            print(f"User ID: {u.id} | Name: {u.full_name} | Active: {u.is_active}")

db.close()
