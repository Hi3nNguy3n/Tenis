from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.models import MarketingBanner, Sponsor
from app.schemas.marketing_schemas import (
    MarketingBannerCreate,
    MarketingBannerUpdate,
    SponsorCreate,
    SponsorUpdate,
)


def _active_window_filter(model, query):
    now = datetime.utcnow()
    return query.filter(
        model.is_active == True,
        or_(model.start_at == None, model.start_at <= now),
        or_(model.end_at == None, model.end_at >= now),
    )


def list_banners(
    db: Session,
    placement: Optional[str] = None,
    only_active: bool = False,
    skip: int = 0,
    limit: int = 100,
):
    query = db.query(MarketingBanner)
    if placement:
        query = query.filter(MarketingBanner.placement == placement)
    if only_active:
        query = _active_window_filter(MarketingBanner, query)
    return query.order_by(MarketingBanner.display_order.asc(), MarketingBanner.id.desc()).offset(skip).limit(limit).all()


def get_banner_or_404(db: Session, banner_id: int):
    banner = db.query(MarketingBanner).filter(MarketingBanner.id == banner_id).first()
    if not banner:
        raise HTTPException(status_code=404, detail="Khong tim thay banner")
    return banner


def create_banner(db: Session, payload: MarketingBannerCreate, user_id: Optional[int] = None):
    banner = MarketingBanner(**payload.model_dump(), created_by=user_id, updated_by=user_id)
    db.add(banner)
    db.commit()
    db.refresh(banner)
    return banner


def update_banner(db: Session, banner_id: int, payload: MarketingBannerUpdate, user_id: Optional[int] = None):
    banner = get_banner_or_404(db, banner_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(banner, field, value)
    banner.updated_by = user_id
    db.commit()
    db.refresh(banner)
    return banner


def delete_banner(db: Session, banner_id: int):
    banner = get_banner_or_404(db, banner_id)
    db.delete(banner)
    db.commit()
    return {"message": "Da xoa banner thanh cong"}


def list_sponsors(
    db: Session,
    tier: Optional[str] = None,
    only_active: bool = False,
    skip: int = 0,
    limit: int = 100,
):
    query = db.query(Sponsor)
    if tier:
        query = query.filter(Sponsor.tier == tier)
    if only_active:
        query = _active_window_filter(Sponsor, query)
    return query.order_by(Sponsor.display_order.asc(), Sponsor.id.desc()).offset(skip).limit(limit).all()


def get_sponsor_or_404(db: Session, sponsor_id: int):
    sponsor = db.query(Sponsor).filter(Sponsor.id == sponsor_id).first()
    if not sponsor:
        raise HTTPException(status_code=404, detail="Khong tim thay nha tai tro")
    return sponsor


def create_sponsor(db: Session, payload: SponsorCreate, user_id: Optional[int] = None):
    sponsor = Sponsor(**payload.model_dump(), created_by=user_id, updated_by=user_id)
    db.add(sponsor)
    db.commit()
    db.refresh(sponsor)
    return sponsor


def update_sponsor(db: Session, sponsor_id: int, payload: SponsorUpdate, user_id: Optional[int] = None):
    sponsor = get_sponsor_or_404(db, sponsor_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(sponsor, field, value)
    sponsor.updated_by = user_id
    db.commit()
    db.refresh(sponsor)
    return sponsor


def delete_sponsor(db: Session, sponsor_id: int):
    sponsor = get_sponsor_or_404(db, sponsor_id)
    db.delete(sponsor)
    db.commit()
    return {"message": "Da xoa nha tai tro thanh cong"}
