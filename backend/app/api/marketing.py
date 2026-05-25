from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.deps import get_current_admin
from app.core.audit import audit_log
from app.crud import crud_marketing
from app.db.database import get_db
from app.models.models import User
from app.schemas.marketing_schemas import (
    MarketingBannerCreate,
    MarketingBannerResponse,
    MarketingBannerUpdate,
    SponsorCreate,
    SponsorResponse,
    SponsorUpdate,
)

router = APIRouter()


@router.get("/banners", response_model=List[MarketingBannerResponse])
def read_public_banners(
    placement: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return crud_marketing.list_banners(db, placement=placement, only_active=True, limit=limit)


@router.get("/sponsors", response_model=List[SponsorResponse])
def read_public_sponsors(
    tier: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return crud_marketing.list_sponsors(db, tier=tier, only_active=True, limit=limit)


@router.get("/admin/banners", response_model=List[MarketingBannerResponse])
def read_admin_banners(
    placement: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return crud_marketing.list_banners(db, placement=placement, skip=skip, limit=limit)


@router.post("/admin/banners", response_model=MarketingBannerResponse)
@audit_log(module="MARKETING", action="CREATE", event_name="Tao banner moi")
def create_admin_banner(
    payload: MarketingBannerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return crud_marketing.create_banner(db, payload, user_id=current_user.id)


@router.put("/admin/banners/{banner_id}", response_model=MarketingBannerResponse)
@audit_log(module="MARKETING", action="UPDATE", event_name="Cap nhat banner")
def update_admin_banner(
    banner_id: int,
    payload: MarketingBannerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return crud_marketing.update_banner(db, banner_id, payload, user_id=current_user.id)


@router.delete("/admin/banners/{banner_id}")
@audit_log(module="MARKETING", action="DELETE", event_name="Xoa banner")
def delete_admin_banner(
    banner_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return crud_marketing.delete_banner(db, banner_id)


@router.get("/admin/sponsors", response_model=List[SponsorResponse])
def read_admin_sponsors(
    tier: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return crud_marketing.list_sponsors(db, tier=tier, skip=skip, limit=limit)


@router.post("/admin/sponsors", response_model=SponsorResponse)
@audit_log(module="MARKETING", action="CREATE", event_name="Tao nha tai tro moi")
def create_admin_sponsor(
    payload: SponsorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return crud_marketing.create_sponsor(db, payload, user_id=current_user.id)


@router.put("/admin/sponsors/{sponsor_id}", response_model=SponsorResponse)
@audit_log(module="MARKETING", action="UPDATE", event_name="Cap nhat nha tai tro")
def update_admin_sponsor(
    sponsor_id: int,
    payload: SponsorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return crud_marketing.update_sponsor(db, sponsor_id, payload, user_id=current_user.id)


@router.delete("/admin/sponsors/{sponsor_id}")
@audit_log(module="MARKETING", action="DELETE", event_name="Xoa nha tai tro")
def delete_admin_sponsor(
    sponsor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    return crud_marketing.delete_sponsor(db, sponsor_id)
