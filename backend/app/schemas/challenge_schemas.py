from pydantic import BaseModel
from datetime import date
from typing import Optional

class ChallengeCreate(BaseModel):
    challenged_id: int  # ID người bị thách đấu
    challenger_partner_id: Optional[int] = None
    challenged_partner_id: Optional[int] = None
    match_type: Optional[str] = "singles"
    proposed_date: date # Ngày muốn đấu
    notes: Optional[str] = None

class ChallengeUpdateStatus(BaseModel):
    status: str # accepted, rejected