from app.db.database import SessionLocal
from app.models.models import Match
import json

db = SessionLocal()
matches = db.query(Match).filter(Match.tournament_id == 19).all()
print(f"Total matches for tournament 19: {len(matches)}")
for m in matches:
    print(f"Match ID: {m.id}, Category ID: {m.tournament_category_id}, Round: {m.round_code}, Status: {m.status}")
db.close()
