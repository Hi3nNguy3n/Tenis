# backend/app/schemas/registration_schemas.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from typing import List

class TeamMember(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    account_code: Optional[str] = None

class RegistrationBase(BaseModel):
    tournament_id: int
    registrant_type: str = "player" # Mặc định là cá nhân ('player' hoặc 'team')
    player_id: Optional[int] = None
    team_id: Optional[int] = None
    notes: Optional[str] = None
    partner_name: Optional[str] = None
    partner_phone: Optional[str] = None
    partner_email: Optional[str] = None
    partner_user_id: Optional[int] = None
    team_members_data: Optional[List[TeamMember]] = None

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
    category_id: Optional[int] = None
    
    # Optional fields for display
    player_name: Optional[str] = None
    user_id: Optional[int] = None
    partner_name: Optional[str] = None
    partner_user_id: Optional[int] = None
    partner_avatar: Optional[str] = None
    category_name: Optional[str] = None
    tournament_name: Optional[str] = None
    location: Optional[str] = None
    
    # Detailed fields for "View Details"
    tournament_date: Optional[date] = None
    category_type: Optional[str] = None
    entry_fee: Optional[float] = None
    entry_fee_team: Optional[float] = None
    player_phone: Optional[str] = None
    player_email: Optional[str] = None
    player_skill: Optional[str] = None
    
    class Config:
        from_attributes = True
