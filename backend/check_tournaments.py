
from app.db.database import SessionLocal
from app.models.models import Tournament

db = SessionLocal()
tournaments = db.query(Tournament).all()
for t in tournaments:
    print(f"ID: {t.id} | Name: {t.name} | Category: {t.category_type} | Format: {t.format_type}")
db.close()
