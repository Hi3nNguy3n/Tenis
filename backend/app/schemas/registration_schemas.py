# backend/app/schemas/registration_schemas.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RegistrationBase(BaseModel):
    tournament_id: int
    registrant_type: str = "player" # Mặc định là cá nhân ('player' hoặc 'team')
    player_id: Optional[int] = None
    team_id: Optional[int] = None
    notes: Optional[str] = None

class RegistrationCreate(RegistrationBase):
    pass

class RegistrationResponse(RegistrationBase):
    id: int
    tournament_id: int
    registrant_type: str
    player_id: Optional[int] = None
    team_id: Optional[int] = None
    status: str
    payment_status: str
    hold_expires_at: Optional[datetime] = None
    registered_at: datetime
    qr_code_url: Optional[str] = None
    
    class Config:
        from_attributes = True