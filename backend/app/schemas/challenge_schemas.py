from pydantic import BaseModel
from datetime import date
from typing import Optional

class ChallengeCreate(BaseModel):
    challenged_id: int  # ID người bị thách đấu
    proposed_date: date # Ngày muốn đấu
    notes: Optional[str] = None

class ChallengeUpdateStatus(BaseModel):
    status: str # accepted, rejected