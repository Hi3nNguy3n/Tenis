from app.db.database import SessionLocal
from app.models.models import TournamentCategory
import json

db = SessionLocal()
cats = db.query(TournamentCategory).filter(TournamentCategory.tournament_id == 19).all()
print(f"Categories for tournament 19:")
for c in cats:
    print(f"ID: {c.id}")
db.close()
