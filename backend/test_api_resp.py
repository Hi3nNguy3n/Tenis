import json
from app.db.database import SessionLocal
from app.crud import crud_tournament
from app.schemas import tournament_schemas

db = SessionLocal()
try:
    tournament_id = 14
    t = crud_tournament.get_tournament_with_count(db, tournament_id=tournament_id)
    # Serialize using Pydantic
    resp = tournament_schemas.TournamentResponse.model_validate(t)
    print(json.dumps(resp.model_dump(), indent=2, default=str))
finally:
    db.close()
