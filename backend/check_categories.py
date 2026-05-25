import sys
import io

# Set stdout to UTF-8 to handle Vietnamese characters
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.db.database import SessionLocal
from app.models.models import Tournament, TournamentCategory

db = SessionLocal()
try:
    tournament_id = 14
    t = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if t:
        print(f"Tournament: {t.name}")
        categories = db.query(TournamentCategory).filter(TournamentCategory.tournament_id == tournament_id).all()
        print(f"Categories count: {len(categories)}")
        for cat in categories:
            print(f" - ID: {cat.id}, Name: {cat.name}, Type: {cat.category_type}")
    else:
        print("Tournament not found")
finally:
    db.close()
