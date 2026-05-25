# backend/app/crud/crud_tournament.py
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List, Dict, Any
from sqlalchemy import func, desc, or_
from fastapi import HTTPException
from datetime import datetime
import math
import random

from app.models.models import Tournament, Match, Registration, Player, User, Payment, Court, MailCampaign, TournamentCategory
from app.schemas.tournament_schemas import TournamentCreate, TournamentUpdate, MatchScoreUpdate, MatchScheduleUpdate, GenerateDrawRequest, ManualMatchCreate, AdminMatchUpdate
from app.core.audit import log_action

import io
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

def create_tournament(db: Session, tournament: TournamentCreate):
    # 1. KIá»‚M TRA TRÃ™NG SLUG TRÆ¯á»šC KHI LÆ¯U
    existing_slug = db.query(Tournament).filter(Tournament.slug == tournament.slug).first()
    if existing_slug:
        # Náº¿u trÃ¹ng, tráº£ vá» lá»—i 400 (Bad Request) thay vÃ¬ Ä‘á»ƒ DB sáº­p (500)
        raise HTTPException(
            status_code=400, 
            detail="ÄÆ°á»ng dáº«n (Slug) nÃ y Ä‘Ã£ Ä‘Æ°á»£c sá»­ dá»¥ng cho má»™t giáº£i Ä‘áº¥u khÃ¡c. Vui lÃ²ng chá»n Ä‘Æ°á»ng dáº«n khÃ¡c!"
        )

    # 2. Náº¾U KHÃ”NG TRÃ™NG THÃŒ Má»šI CHO Táº O
    db_tournament = Tournament(**tournament.model_dump())
    db.add(db_tournament)
    db.commit()
    db.refresh(db_tournament)
    return db_tournament

def delete_tournament_db(db: Session, tournament_id: int):
    """XÃ³a toÃ n bá»™ giáº£i Ä‘áº¥u vÃ  cÃ¡c dá»¯ liá»‡u liÃªn quan (Cascade manual)"""
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="KhÃ´ng tÃ¬m tháº¥y giáº£i Ä‘áº¥u Ä‘á»ƒ xÃ³a.")

    # 1. XÃ³a cÃ¡c tráº­n Ä‘áº¥u liÃªn quan
    db.query(Match).filter(Match.tournament_id == tournament_id).delete()
    
    # 2. XÃ³a cÃ¡c lÆ°á»£t Ä‘Äƒng kÃ½
    db.query(Registration).filter(Registration.tournament_id == tournament_id).delete()
    
    # 3. XÃ³a cÃ¡c ná»™i dung thi Ä‘áº¥u
    db.query(TournamentCategory).filter(TournamentCategory.tournament_id == tournament_id).delete()
    
    # 4. XÃ³a cÃ¡c chiáº¿n dá»‹ch email
    db.query(MailCampaign).filter(MailCampaign.tournament_id == tournament_id).delete()

    # 5. Cuá»‘i cÃ¹ng má»›i xÃ³a giáº£i Ä‘áº¥u
    db.delete(tournament)
    db.commit()
    return {"message": "ÄÃ£ xÃ³a giáº£i Ä‘áº¥u thÃ nh cÃ´ng!", "id": tournament_id}


def get_tournaments_with_counts(db: Session, skip: int = 0, limit: int = 10, status: str = None):
    query = db.query(Tournament).options(joinedload(Tournament.categories))
    if status:
        query = query.filter(Tournament.status == status)
    
    tournaments = query.offset(skip).limit(limit).all()
    
    # TÃ­nh sá»‘ slot Ä‘Ã£ Ä‘Äƒng kÃ½ cho tá»«ng giáº£i
    for t in tournaments:
        t.current_participants = db.query(Registration).filter(
            Registration.tournament_id == t.id,
            Registration.status.in_(["confirmed", "pending"]),
            Registration.deleted_at.is_(None)
        ).count()
    return tournaments

def get_tournament_with_count(db: Session, tournament_id: int):
    t = db.query(Tournament).options(joinedload(Tournament.categories)).filter(Tournament.id == tournament_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="KhÃ´ng tÃ¬m tháº¥y giáº£i Ä‘áº¥u")
    
    t.current_participants = db.query(Registration).filter(
        Registration.tournament_id == t.id,
        Registration.status.in_(["confirmed", "pending"]),
        Registration.deleted_at.is_(None)
    ).count()
    return t

def get_system_stats(db: Session):
    total_tournaments = db.query(Tournament).count()
    total_registrations = db.query(Registration).count()
    active_tournaments = db.query(Tournament).filter(Tournament.status == "ongoing").count()
    pending_approvals = db.query(Registration).filter(Registration.status == "pending").count()
    
    revenue = db.query(func.sum(Payment.amount)).filter(Payment.status == "completed").scalar() or 0
    
    total_matches = db.query(Match).count()
    completed_matches = db.query(Match).filter(Match.status == "completed").count()
    
    completion_rate = 0
    if total_matches > 0:
        completion_rate = round((completed_matches / total_matches) * 100, 1)
        
    return {
        "total_tournaments": total_tournaments,
        "total_registrations": total_registrations,
        "active_tournaments": active_tournaments,
        "pending_approvals": pending_approvals,
        "revenue": float(revenue),
        "total_matches": total_matches,
        "completed_matches": completed_matches,
        "completion_rate": completion_rate
    }

def update_tournament_info(db: Session, tournament_id: int, tournament_in: TournamentCreate, admin_id: int):
    db_tour = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not db_tour:
        raise HTTPException(status_code=404, detail="KhÃ´ng tÃ¬m tháº¥y giáº£i Ä‘áº¥u")

    today = datetime.utcnow().date()
    if tournament_in.start_date and tournament_in.start_date < today:
        raise HTTPException(status_code=400, detail="NgÃ y khai máº¡c khÃ´ng Ä‘Æ°á»£c náº±m trong quÃ¡ khá»©.")
    if tournament_in.end_date and tournament_in.start_date and tournament_in.end_date < tournament_in.start_date:
        raise HTTPException(status_code=400, detail="NgÃ y káº¿t thÃºc pháº£i sau ngÃ y khai máº¡c.")

    for var, value in vars(tournament_in).items():
        setattr(db_tour, var, value)
        
    db.commit()
    db.refresh(db_tour)
    
    log_action(db, admin_id, "TOURNAMENT", "UPDATE", "Tournament", db_tour.id, None, {"name": db_tour.name}, "Cáº­p nháº­t giáº£i Ä‘áº¥u")
    return db_tour

def generate_knockout_draw(db: Session, tournament_id: int, category_id: Optional[int] = None, draw_size: Optional[int] = None, round_names: Optional[List[str]] = None):
    query = db.query(Registration).filter(
        Registration.tournament_id == tournament_id,
        Registration.status.in_(["pending", "approved", "confirmed", "paid", "checked_in"]),
        Registration.deleted_at.is_(None)
    )
    if category_id:
        query = query.filter(Registration.tournament_category_id == category_id)
    regs = query.all()

    # In manual bracket mode, draw_size means participant/team count.
    # Example: 21 teams -> round 1 shows 11 bracket nodes: 10 full matches
    # plus 1 bye branch that admins can complete manually.
    participant_count = draw_size if draw_size and draw_size > 0 else len(regs)
    if participant_count <= 1:
        raise HTTPException(status_code=400, detail="Khong du so doi de tao nhanh dau.")

    round_match_counts = []
    current_participants = participant_count
    while current_participants > 1:
        current_matches = math.ceil(current_participants / 2)
        round_match_counts.append(current_matches)
        current_participants = current_matches
    rounds_needed = len(round_match_counts)

    round_labels = {1: "FINAL", 2: "SF", 4: "QF", 8: "R16", 16: "R32", 32: "R64", 64: "R128"}

    match_del_query = db.query(Match).filter(Match.tournament_id == tournament_id, Match.stage_type == "knockout")
    if category_id:
        match_del_query = match_del_query.filter(Match.tournament_category_id == category_id)
    match_del_query.delete()
    db.flush()

    matches_by_round = {}
    for round_index, num_matches in enumerate(round_match_counts):
        matches_by_round[round_index] = []
        custom_label = round_names[round_index].strip() if round_names and round_index < len(round_names) and round_names[round_index] else None
        label = custom_label or round_labels.get(num_matches, f"R{num_matches * 2}")

        for i in range(num_matches):
            m = Match(
                tournament_id=tournament_id,
                tournament_category_id=category_id,
                stage_type="knockout",
                round_code=label,
                match_no=i + 1,
                status="pending",
                best_of_sets=3,
                elo_affected=True
            )
            db.add(m)
            matches_by_round[round_index].append(m)

    db.flush()

    # Link winners to the earliest available future match. This keeps the tree
    # valid even for odd participant counts where one side receives a bye.
    incoming_counts = {}
    for round_index in range(0, rounds_needed - 1):
        current_round = matches_by_round[round_index]
        for match in current_round:
            linked = False
            for future_round in range(round_index + 1, rounds_needed):
                for future_match in matches_by_round[future_round]:
                    current_incoming = incoming_counts.get(future_match.id, 0)
                    if current_incoming < 2:
                        match.next_match_id = future_match.id
                        incoming_counts[future_match.id] = current_incoming + 1
                        linked = True
                        break
                if linked:
                    break

    for m in matches_by_round[0]:
        m.side_a_registration_id = None
        m.side_b_registration_id = None

    db.commit()

    return {
        "message": "Da tao khung nhanh dau thanh cong. Vui long tu ghep cap thi dau bang tay.",
        "total_slots": participant_count,
        "first_round_matches": round_match_counts[0],
        "participant_count": participant_count,
        "rounds": rounds_needed
    }
def get_tournament_matches_detail(db: Session, tournament_id: int, category_id: Optional[int] = None):
    query = db.query(Match).filter(Match.tournament_id == tournament_id)
    if category_id:
        query = query.filter(Match.tournament_category_id == category_id)
    
    matches = query.order_by(Match.match_no).all()
    results = []
    for m in matches:
        p1_name = "Chua xac dinh"
        p2_name = "Chua xac dinh"
        p1_partner_name = None
        p2_partner_name = None
        p1_user_id = None
        p2_user_id = None
        p1_avatar = None
        p2_avatar = None
        p1_partner_user_id = None
        p1_partner_avatar = None
        p2_partner_user_id = None
        p2_partner_avatar = None
        
        reg_a = db.query(Registration).filter(Registration.id == m.side_a_registration_id).first() if m.side_a_registration_id else None
        if reg_a:
            p_a = db.query(Player).filter(Player.id == reg_a.player_id).first()
            if p_a:
                p1_user_id = p_a.user_id
                user_a = db.query(User).filter(User.id == p_a.user_id).first()
                if user_a:
                    p1_name = user_a.full_name
                    p1_avatar = user_a.avatar_url
            p1_partner_name = reg_a.partner_name
            p1_partner_user_id = reg_a.partner_user_id
            if p1_partner_user_id:
                user_partner_a = db.query(User).filter(User.id == p1_partner_user_id).first()
                if user_partner_a:
                    p1_partner_avatar = user_partner_a.avatar_url
                    p1_partner_name = user_partner_a.full_name # Override with user name if available

        reg_b = db.query(Registration).filter(Registration.id == m.side_b_registration_id).first() if m.side_b_registration_id else None
        if reg_b:
            p_b = db.query(Player).filter(Player.id == reg_b.player_id).first()
            if p_b:
                p2_user_id = p_b.user_id
                user_b = db.query(User).filter(User.id == p_b.user_id).first()
                if user_b:
                    p2_name = user_b.full_name
                    p2_avatar = user_b.avatar_url
            p2_partner_name = reg_b.partner_name
            p2_partner_user_id = reg_b.partner_user_id
            if p2_partner_user_id:
                user_partner_b = db.query(User).filter(User.id == p2_partner_user_id).first()
                if user_partner_b:
                    p2_partner_avatar = user_partner_b.avatar_url
                    p2_partner_name = user_partner_b.full_name # Override with user name if available
        
        court_name = db.query(Court.court_name).filter(Court.id == m.court_id).scalar() if m.court_id else None
                
        results.append({
            "id": m.id, "round_code": m.round_code, "match_no": m.match_no,
            "side_a_registration_id": m.side_a_registration_id,
            "side_b_registration_id": m.side_b_registration_id,
            "p1_name": p1_name, "p2_name": p2_name,
            "p1_avatar": p1_avatar, "p2_avatar": p2_avatar,
            "p1_partner_name": p1_partner_name, "p1_partner_user_id": p1_partner_user_id, "p1_partner_avatar": p1_partner_avatar,
            "p2_partner_name": p2_partner_name, "p2_partner_user_id": p2_partner_user_id, "p2_partner_avatar": p2_partner_avatar,
            "status": m.status,
            "court_id": m.court_id, 
            "court": court_name,
            "start_time": m.start_time.isoformat() if m.start_time else None, 
            "winner_side": m.winner_side,
            "score_a": m.set1_a,
            "score_b": m.set1_b,
            "p1_user_id": p1_user_id,
            "p2_user_id": p2_user_id,
            "referee_id": m.referee_id,
            "referee_name": m.referee_name,
            "referee_phone": m.referee_phone,
            "score_summary": getattr(m, 'score_summary', None) or getattr(m, 'result_note', None),
            "video_url": getattr(m, 'video_url', None),
            "live_stream_url": getattr(m, 'live_stream_url', None),
            "image_url": getattr(m, 'image_url', None),
            "advance_note": getattr(m, 'win_reason', None),
            "stage_type": m.stage_type,
            "group_id": m.group_id,
            "next_match_id": m.next_match_id,
            "tournament_category_id": m.tournament_category_id
        })
    return results

def _auto_link_manual_match(db: Session, match: Match):
    if match.stage_type not in ["knockout", "playoff"]:
        return

    base_query = db.query(Match).filter(
        Match.tournament_id == match.tournament_id,
        Match.stage_type == match.stage_type,
        Match.id != match.id
    )
    if match.tournament_category_id:
        base_query = base_query.filter(Match.tournament_category_id == match.tournament_category_id)

    all_matches = base_query.all()
    if not all_matches:
        return

    rounds_map = {}
    for item in all_matches + [match]:
        rounds_map.setdefault(item.round_code, []).append(item)

    ordered_rounds = sorted(
        rounds_map.items(),
        key=lambda entry: (-len(entry[1]), min((m.match_no or 0) for m in entry[1]))
    )
    round_codes = [round_code for round_code, _ in ordered_rounds]
    if match.round_code not in round_codes:
        return

    current_index = round_codes.index(match.round_code)
    desired_parent_match_no = math.ceil((match.match_no or 1) / 2)

    if current_index + 1 < len(round_codes):
        parent_round_code = round_codes[current_index + 1]
        parent_match = next(
            (
                candidate for candidate in rounds_map[parent_round_code]
                if (candidate.match_no or 0) == desired_parent_match_no
            ),
            None
        )
        if parent_match:
            match.next_match_id = parent_match.id

    if current_index > 0:
        child_round_code = round_codes[current_index - 1]
        candidate_children = sorted(
            [
                candidate for candidate in rounds_map[child_round_code]
                if math.ceil((candidate.match_no or 1) / 2) == (match.match_no or 1)
            ],
            key=lambda candidate: candidate.match_no or 0
        )
        incoming = db.query(func.count(Match.id)).filter(Match.next_match_id == match.id).scalar() or 0
        for child in candidate_children:
            if incoming >= 2:
                break
            if child.next_match_id in [None, match.next_match_id]:
                child.next_match_id = match.id
                incoming += 1

def validate_next_match_assignment(db: Session, match: Match, next_match_id: Optional[int]):
    if not next_match_id:
        return
    if next_match_id == match.id:
        raise HTTPException(status_code=400, detail="Khong the noi tran dau den chinh no.")

    next_match = db.query(Match).filter(Match.id == next_match_id).first()
    if not next_match:
        raise HTTPException(status_code=404, detail="Khong tim thay tran dau tiep theo.")
    if next_match.tournament_id != match.tournament_id:
        raise HTTPException(status_code=400, detail="Tran dau tiep theo phai thuoc cung giai dau.")
    if match.tournament_category_id and next_match.tournament_category_id and next_match.tournament_category_id != match.tournament_category_id:
        raise HTTPException(status_code=400, detail="Tran dau tiep theo phai thuoc cung noi dung.")

    visited = {match.id}
    cursor = next_match
    while cursor and cursor.next_match_id:
        if cursor.next_match_id in visited:
            raise HTTPException(status_code=400, detail="Lien ket nhanh dau tao vong lap.")
        visited.add(cursor.id)
        cursor = db.query(Match).filter(Match.id == cursor.next_match_id).first()

def _advance_winner_to_next_match(db: Session, match: Match, win_reg_id: Optional[int]):
    if not win_reg_id or not match.tournament_id or not match.next_match_id:
        return

    next_m = db.query(Match).filter(Match.id == match.next_match_id).first()
    if not next_m:
        return

    sibling_matches = db.query(Match).filter(
        Match.next_match_id == next_m.id,
        Match.tournament_id == match.tournament_id
    ).order_by(Match.match_no.asc(), Match.id.asc()).all()

    target_side = None
    for index, sibling in enumerate(sibling_matches):
        if sibling.id == match.id:
            target_side = "side_a" if index % 2 == 0 else "side_b"
            break

    if target_side == "side_a":
        next_m.side_a_registration_id = win_reg_id
    elif target_side == "side_b":
        next_m.side_b_registration_id = win_reg_id
    elif not next_m.side_a_registration_id:
        next_m.side_a_registration_id = win_reg_id
    elif not next_m.side_b_registration_id:
        next_m.side_b_registration_id = win_reg_id
    else:
        next_m.side_a_registration_id = win_reg_id

def create_manual_match_db(db: Session, tournament_id: int, payload: ManualMatchCreate):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Khong tim thay giai dau")
    if payload.next_match_id:
        next_match = db.query(Match).filter(Match.id == payload.next_match_id).first()
        if not next_match:
            raise HTTPException(status_code=404, detail="Khong tim thay tran dau tiep theo.")
        if next_match.tournament_id != tournament_id:
            raise HTTPException(status_code=400, detail="Tran dau tiep theo phai thuoc cung giai dau.")
        if payload.category_id and next_match.tournament_category_id and next_match.tournament_category_id != payload.category_id:
            raise HTTPException(status_code=400, detail="Tran dau tiep theo phai thuoc cung noi dung.")

    category_id = payload.category_id
    round_code = (payload.round_code or "Vong moi").strip()
    stage_type = payload.stage_type or "knockout"
    max_no_query = db.query(func.max(Match.match_no)).filter(
        Match.tournament_id == tournament_id,
        Match.stage_type == stage_type,
        Match.round_code == round_code
    )
    if category_id:
        max_no_query = max_no_query.filter(Match.tournament_category_id == category_id)
    next_no = (max_no_query.scalar() or 0) + 1

    match = Match(
        tournament_id=tournament_id,
        tournament_category_id=category_id,
        stage_type=stage_type,
        round_code=round_code,
        match_no=payload.match_no or next_no,
        side_a_registration_id=payload.side_a_registration_id,
        side_b_registration_id=payload.side_b_registration_id,
        status=payload.status or "pending",
        court_id=payload.court_id,
        start_time=payload.start_time,
        referee_name=payload.referee_name or None,
        referee_phone=payload.referee_phone or None,
        live_stream_url=payload.live_stream_url or None,
        next_match_id=payload.next_match_id,
        best_of_sets=3,
        elo_affected=True,
    )
    db.add(match)
    db.flush()
    source_ids = payload.source_match_ids or []
    if source_ids:
        source_matches = db.query(Match).filter(
            Match.id.in_(source_ids),
            Match.tournament_id == tournament_id
        ).all()
        for source in source_matches:
            source.next_match_id = match.id
    if not payload.next_match_id and not source_ids:
        _auto_link_manual_match(db, match)
    db.commit()
    db.refresh(match)
    return {"message": "ÄÃ£ thÃªm tráº­n thá»§ cÃ´ng vÃ o nhÃ¡nh Ä‘áº¥u", "id": match.id}

def update_match_admin_db(db: Session, match_id: int, payload: AdminMatchUpdate):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="KhÃ´ng tÃ¬m tháº¥y tráº­n Ä‘áº¥u")

    data = payload.model_dump(exclude_unset=True)
    if data.get("side_a_registration_id") and data.get("side_a_registration_id") == data.get("side_b_registration_id"):
        raise HTTPException(status_code=400, detail="KhÃ´ng thá»ƒ xáº¿p cÃ¹ng má»™t VÄV/cáº·p Ä‘áº¥u á»Ÿ cáº£ hai bÃªn.")
    if "next_match_id" in data:
        validate_next_match_assignment(db, match, data["next_match_id"])

    for field in [
        "round_code", "match_no", "stage_type", "side_a_registration_id", "side_b_registration_id",
        "status", "court_id", "start_time", "referee_name", "referee_phone",
        "live_stream_url", "video_url", "image_url", "winner_side", "next_match_id"
    ]:
        if field in data:
            setattr(match, field, data[field])

    if "advance_note" in data:
        match.win_reason = (data["advance_note"] or None)

    if "score" in data:
        match.result_note = data["score"]
        match.score_summary = data["score"]

    if data.get("winner_side"):
        match.winner_registration_id = match.side_a_registration_id if data["winner_side"] == "side_a" else match.side_b_registration_id
        _advance_winner_to_next_match(db, match, match.winner_registration_id)

    db.commit()
    return {"message": "ÄÃ£ cáº­p nháº­t thÃ´ng tin Ä‘iá»u hÃ nh tráº­n Ä‘áº¥u"}

def delete_match_from_draw_db(db: Session, match_id: int):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Khong tim thay tran dau")

    db.query(Match).filter(Match.next_match_id == match_id).update(
        {Match.next_match_id: match.next_match_id},
        synchronize_session=False
    )
    db.delete(match)
    db.commit()
    return {"message": "Da xoa khung tran dau khoi so do"}

def schedule_match_db(db: Session, match_id: int, payload: MatchScheduleUpdate):
    db_match = db.query(Match).filter(Match.id == match_id).first()
    if not db_match:
        raise HTTPException(status_code=404, detail="KhÃ´ng tÃ¬m tháº¥y tráº­n Ä‘áº¥u")
    
    tournament = db.query(Tournament).filter(Tournament.id == db_match.tournament_id).first()
    if tournament:
        schedule_date = payload.start_time.date()
        if tournament.start_date and schedule_date < tournament.start_date:
            raise HTTPException(status_code=400, detail=f"Giáº£i Ä‘áº¥u báº¯t Ä‘áº§u tá»« ngÃ y {tournament.start_date.strftime('%d/%m/%Y')}.")
        if tournament.end_date and schedule_date > tournament.end_date:
            raise HTTPException(status_code=400, detail=f"Giáº£i Ä‘áº¥u káº¿t thÃºc vÃ o ngÃ y {tournament.end_date.strftime('%d/%m/%Y')}.")
            
    db_match.court_id = payload.court_id
    db_match.start_time = payload.start_time
    if payload.referee_id:
        db_match.referee_id = payload.referee_id
    db_match.referee_name = payload.referee_name
    db_match.referee_phone = payload.referee_phone
    db.commit()
    return {"message": "ÄÃ£ cáº­p nháº­t lá»‹ch thi Ä‘áº¥u"}

def get_all_matches_detail(db: Session, limit: Optional[int] = None):
    query = db.query(Match, Tournament, Court).outerjoin(
        Tournament, Match.tournament_id == Tournament.id
    ).outerjoin(
        Court, Match.court_id == Court.id
    ).order_by(desc(Match.start_time))
    if limit:
        query = query.limit(limit)
    matches = query.all()

    # Helper láº¥y thÃ´ng tin Ä‘áº§y Ä‘á»§ cá»§a team tá»« match vÃ  side
    def get_match_players_data(m, side):
        if side == "a":
            reg_id = m.side_a_registration_id
            p_id = m.player_a_id
            p2_id = m.player_a2_id
        else:
            reg_id = m.side_b_registration_id
            p_id = m.player_b_id
            p2_id = m.player_b2_id

        data = {"name": None, "avatar": None, "partner_name": None, "partner_avatar": None}

        # CÃ¡ch 1: Qua registration (cho giáº£i Ä‘áº¥u)
        if reg_id:
            reg = db.query(Registration).filter(Registration.id == reg_id).first()
            if reg:
                user = db.query(User).join(Player, Player.user_id == User.id).filter(Player.id == reg.player_id).first()
                data["name"] = user.full_name if user else None
                data["avatar"] = user.avatar_url if user else None
                data["partner_name"] = reg.partner_name
                
                if reg.partner_user_id:
                    p_user = db.query(User).filter(User.id == reg.partner_user_id).first()
                    if p_user:
                        data["partner_avatar"] = p_user.avatar_url
                elif getattr(reg, "partner_player_id", None):
                    p_user = db.query(User).join(Player).filter(Player.id == reg.partner_player_id).first()
                    if p_user:
                        data["partner_avatar"] = p_user.avatar_url
            return data

        # CÃ¡ch 2: Qua direct player_id (cho tráº­n giao há»¯u/thÃ¡ch Ä‘áº¥u)
        if p_id:
            user = db.query(User).join(Player, Player.user_id == User.id).filter(Player.id == p_id).first()
            if user:
                data["name"] = user.full_name
                data["avatar"] = user.avatar_url

        if p2_id:
            user2 = db.query(User).join(Player, Player.user_id == User.id).filter(Player.id == p2_id).first()
            if user2:
                data["partner_name"] = user2.full_name
                data["partner_avatar"] = user2.avatar_url

        return data

    results = []
    for m, t, c in matches:
        # Æ¯u tiÃªn match_date cá»§a tráº­n, fallback vá» start_time.date(), cuá»‘i cÃ¹ng lÃ  start_date giáº£i
        if m.match_date:
            match_date = m.match_date
        elif m.start_time:
            match_date = m.start_time.date()
        else:
            match_date = t.start_date if t else None

        p1_data = get_match_players_data(m, "a")
        p2_data = get_match_players_data(m, "b")

        results.append({
            "id": m.id,
            "tournament_id": t.id if t else None,
            "tournament": t.name if t else "Giao há»¯u tá»± do",
            "tournament_start_date": t.start_date.isoformat() if t and t.start_date else None,
            "tournament_end_date": t.end_date.isoformat() if t and t.end_date else None,
            "location": (t.location if t else None) or "Saigon Tennis Club",
            "round_code": m.round_code,
            "court": c.court_name if c else "Chua gan san",
            "date": match_date.isoformat() if match_date else None,
            "start_time": m.start_time.isoformat() if m.start_time else None,
            "start": m.start_time.strftime("%H:%M") if m.start_time else "--:--",
            "status": m.status,
            "p1_name": p1_data["name"],
            "p1_avatar": p1_data["avatar"],
            "p1_partner_name": p1_data["partner_name"],
            "p1_partner_avatar": p1_data["partner_avatar"],
            "p2_name": p2_data["name"],
            "p2_avatar": p2_data["avatar"],
            "p2_partner_name": p2_data["partner_name"],
            "p2_partner_avatar": p2_data["partner_avatar"],
            "winner_side": m.winner_side,
            "score": m.score_summary,
            "video_url": getattr(m, 'video_url', None),
        })
    return results

def calculate_elo_and_update_match(db: Session, match_id: int, payload: MatchScoreUpdate):
    # 1. TÃ¬m tráº­n Ä‘áº¥u vÃ  kiá»ƒm tra tráº¡ng thÃ¡i
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match or match.status == "completed":
        raise HTTPException(status_code=400, detail="Tráº­n Ä‘áº¥u khÃ´ng tá»“n táº¡i hoáº·c Ä‘Ã£ káº¿t thÃºc.")

    # 0. Kiá»ƒm tra xem tráº­n Ä‘áº¥u cÃ³ Ä‘Æ°á»£c phÃ©p tÃ­nh ELO khÃ´ng
    if not getattr(match, 'elo_affected', False):
        # Náº¿u khÃ´ng tÃ­nh ELO, chÃºng ta chá»‰ cáº­p nháº­t tráº¡ng thÃ¡i tráº­n Ä‘áº¥u
        match.status = "completed"
        match.score_summary = payload.score
        match.winner_side = payload.winner_side
        if payload.referee_id:
            match.referee_id = payload.referee_id
        match.referee_name = payload.referee_name
        match.referee_phone = payload.referee_phone
        db.commit()
        return {"message": "Cáº­p nháº­t tá»· sá»‘ thÃ nh cÃ´ng (KhÃ´ng tÃ­nh ELO)"}

    # 1. Láº¤Y PLAYER ID Cá»¦A 2 BÃŠN
    p1_id = None
    p2_id = None

    if match.tournament_id:
        # TrÆ°á»ng há»£p tráº­n Ä‘áº¥u GIáº¢I: Láº¥y Player ID thÃ´ng qua báº£ng Registration
        reg_a = db.query(Registration).filter(Registration.id == match.side_a_registration_id).first()
        reg_b = db.query(Registration).filter(Registration.id == match.side_b_registration_id).first()
        if reg_a: p1_id = reg_a.player_id
        if reg_b: p2_id = reg_b.player_id
        
        # Fallback: Náº¿u khÃ´ng tÃ¬m tháº¥y qua Registration, láº¥y trá»±c tiáº¿p tá»« match (cho cÃ¡c tráº­n táº¡o thá»§ cÃ´ng)
        if not p1_id: p1_id = match.player_a_id
        if not p2_id: p2_id = match.player_b_id
    else:
        # TrÆ°á»ng há»£p tráº­n GIAO Há»®U: Láº¥y trá»±c tiáº¿p tá»« player_a_id vÃ  player_b_id
        p1_id = match.player_a_id
        p2_id = match.player_b_id

    # 3. Kiá»ƒm tra tÃ­nh Ä‘áº§y Ä‘á»§ cá»§a 2 váº­n Ä‘á»™ng viÃªn
    if not p1_id or not p2_id:
        # Náº¿u thiáº¿u 1 bÃªn (láº» Ä‘á»™i, tháº¯ng bye), ta chá»‰ cáº­p nháº­t káº¿t quáº£ mÃ  khÃ´ng tÃ­nh ELO
        match.status = "completed"
        match.winner_side = payload.winner_side
        win_reg_id = match.side_a_registration_id if payload.winner_side == "side_a" else match.side_b_registration_id
        match.winner_registration_id = win_reg_id
        match.result_note = payload.score
        if payload.video_url is not None:
            match.video_url = payload.video_url
        if payload.image_url is not None:
            match.image_url = payload.image_url
        if payload.referee_id:
            match.referee_id = payload.referee_id
        match.referee_name = payload.referee_name
        match.referee_phone = payload.referee_phone
        
        _advance_winner_to_next_match(db, match, win_reg_id)
        
        db.commit()
        return {"message": "Cáº­p nháº­t tá»· sá»‘ thÃ nh cÃ´ng cho tráº­n Ä‘áº¥u láº» (Tháº¯ng bye/Láº» Ä‘á»™i)!"}


    # 4. XÃ¡c Ä‘á»‹nh ai tháº¯ng ai thua dá»±a trÃªn payload gá»­i lÃªn
    win_p_id = p1_id if payload.winner_side == "side_a" else p2_id
    lose_p_id = p2_id if payload.winner_side == "side_a" else p1_id
    
    # XÃ¡c Ä‘á»‹nh registration_id cá»§a ngÆ°á»i tháº¯ng (chá»‰ dÃ¹ng cho logic tiáº¿n vÃ o vÃ²ng sau cá»§a Giáº£i)
    win_reg_id = match.side_a_registration_id if payload.winner_side == "side_a" else match.side_b_registration_id

    winner_p = db.query(Player).filter(Player.id == win_p_id).first()
    loser_p = db.query(Player).filter(Player.id == lose_p_id).first()

    if not winner_p or not loser_p:
        raise HTTPException(status_code=404, detail="KhÃ´ng tÃ¬m tháº¥y há»“ sÆ¡ váº­n Ä‘á»™ng viÃªn.")

    # 5. THUáº¬T TOÃN ELO
    K = 32
    Ra = winner_p.elo_points
    Rb = loser_p.elo_points
    E_winner = 1 / (1 + 10 ** ((Rb - Ra) / 400))
    elo_gain = round(K * (1 - E_winner))
    
    # Cáº­p nháº­t chá»‰ sá»‘ cho ngÆ°á»i tháº¯ng (vÃ  Ä‘á»“ng Ä‘á»™i náº¿u cÃ³)
    def update_p_stats(p, gain, is_win):
        p.elo_points += gain if is_win else -gain
        if is_win: p.wins += 1
        else: p.losses += 1
        p.matches_played += 1

    update_p_stats(winner_p, elo_gain, True)
    update_p_stats(loser_p, elo_gain, False)

    # Náº¿u lÃ  Ä‘Ã¡nh Ä‘Ã´i, cáº­p nháº­t cho cáº£ Ä‘á»“ng Ä‘á»™i
    if match.tournament_id:
        reg_win = db.query(Registration).filter(Registration.id == win_reg_id).first()
        lose_reg_id = match.side_b_registration_id if payload.winner_side == "side_a" else match.side_a_registration_id
        reg_lose = db.query(Registration).filter(Registration.id == lose_reg_id).first()
        
        if reg_win and reg_win.partner_player_id:
            partner_win = db.query(Player).filter(Player.id == reg_win.partner_player_id).first()
            if partner_win: update_p_stats(partner_win, elo_gain, True)
            
        if reg_lose and reg_lose.partner_player_id:
            partner_lose = db.query(Player).filter(Player.id == reg_lose.partner_player_id).first()
            if partner_lose: update_p_stats(partner_lose, elo_gain, False)

    # 6. Cáº­p nháº­t thÃ´ng tin tráº­n Ä‘áº¥u
    match.status = "completed"
    match.winner_side = payload.winner_side
    match.winner_registration_id = win_reg_id # LÆ°u reg_id náº¿u cÃ³
    match.result_note = payload.score
    if payload.video_url is not None:
        match.video_url = payload.video_url
    if payload.image_url is not None:
        match.image_url = payload.image_url
    if payload.referee_id:
        match.referee_id = payload.referee_id
    match.referee_name = payload.referee_name
    match.referee_phone = payload.referee_phone

    # 7. Xá»­ lÃ½ logic thÄƒng háº¡ng náº¿u lÃ  tráº­n Ä‘áº¥u giáº£i[cite: 33]
    message_suffix = ""
    if match.tournament_id:
        # Kiá»ƒm tra xem cÃ²n tráº­n Ä‘áº¥u nÃ o chÆ°a xong khÃ´ng
        remaining_matches = db.query(Match).filter(
            Match.tournament_id == match.tournament_id,
            Match.id != match.id, # Trá»« tráº­n hiá»‡n táº¡i vá»«a xong
            Match.status.in_(["pending", "scheduled", "ongoing"])
        ).count()

        if remaining_matches == 0:
            tournament = db.query(Tournament).filter(Tournament.id == match.tournament_id).first()
            if tournament and tournament.status != "finished":
                tournament.status = "finished"
                # Cáº­p nháº­t ID nhÃ  vÃ´ Ä‘á»‹ch náº¿u lÃ  tráº­n Chung káº¿t
                if match.round_code in ["FINAL", "F"] and hasattr(tournament, 'winner_player_id'):
                    tournament.winner_player_id = winner_p.id
                message_suffix = f" Giáº£i Ä‘áº¥u Ä‘Ã£ chÃ­nh thá»©c khÃ©p láº¡i. ChÃºc má»«ng {winner_p.full_name if hasattr(winner_p, 'full_name') else winner_p.id}!"
        else:
            _advance_winner_to_next_match(db, match, win_reg_id)

    db.commit()
    return {"message": f"Cáº­p nháº­t káº¿t quáº£ thÃ nh cÃ´ng! {message_suffix}"}

def get_public_bracket_detail(db: Session, tournament_id: int, category_id: Optional[int] = None):
    query = db.query(Match).filter(Match.tournament_id == tournament_id)
    if category_id:
        query = query.filter(Match.tournament_category_id == category_id)
    matches = query.all()
    
    def get_player_data(reg_id):
        if not reg_id: return {"name": "Chua xac dinh", "user_id": None, "avatar_url": None, "partner_name": None, "partner_user_id": None, "partner_avatar_url": None}
        reg = db.query(Registration).filter(Registration.id == reg_id).first()
        if not reg: return {"name": "Chua xac dinh", "user_id": None, "avatar_url": None, "partner_name": None, "partner_user_id": None, "partner_avatar_url": None}
        
        user = db.query(User).join(Player).filter(Player.id == reg.player_id).first()
        data = {
            "name": user.full_name if user else "Chua xac dinh",
            "user_id": user.id if user else None,
            "avatar_url": user.avatar_url if user else None,
            "partner_name": None,
            "partner_user_id": None
        }
        
        if reg.partner_user_id:
            partner_user = db.query(User).filter(User.id == reg.partner_user_id).first()
            if partner_user:
                data["partner_name"] = partner_user.full_name
                data["partner_user_id"] = partner_user.id
                data["partner_avatar_url"] = partner_user.avatar_url
        elif getattr(reg, "partner_player_id", None):
            partner_user = db.query(User).join(Player).filter(Player.id == reg.partner_player_id).first()
            if partner_user:
                data["partner_name"] = partner_user.full_name
                data["partner_user_id"] = partner_user.id
                data["partner_avatar_url"] = partner_user.avatar_url
        elif reg.partner_name: 
            data["partner_name"] = reg.partner_name
                
        return data

    results = []
    for m in matches:
        p1_data = get_player_data(m.side_a_registration_id)
        p2_data = get_player_data(m.side_b_registration_id)
        
        court_name = db.query(Court.court_name).filter(Court.id == m.court_id).scalar() if m.court_id else None

        results.append({
            "id": m.id, "match_no": m.match_no, "round_code": m.round_code,
            "category_id": m.tournament_category_id,
            "p1_name": p1_data["name"],
            "p1_user_id": p1_data["user_id"],
            "p1_avatar": p1_data["avatar_url"],
            "p1_partner_name": p1_data["partner_name"],
            "p1_partner_user_id": p1_data["partner_user_id"],
            "p1_partner_avatar": p1_data["partner_avatar_url"],
            
            "p2_name": p2_data["name"],
            "p2_user_id": p2_data["user_id"],
            "p2_avatar": p2_data["avatar_url"],
            "p2_partner_name": p2_data["partner_name"],
            "p2_partner_user_id": p2_data["partner_user_id"],
            "p2_partner_avatar": p2_data["partner_avatar_url"],
            
            "winner_side": m.winner_side, "status": m.status,
            "start_time": m.start_time,
            "match_date": m.match_date,
            "score": m.result_note,
            "score_summary": m.score_summary,
            "score_a": m.set1_a,
            "score_b": m.set1_b,
            "court_id": m.court_id,
            "court": court_name,
            "live_stream_url": getattr(m, "live_stream_url", None),
            "video_url": getattr(m, "video_url", None),
            "image_url": getattr(m, "image_url", None),
            "advance_note": getattr(m, "win_reason", None),
            "referee_name": m.referee_name or (db.query(User.full_name).filter(User.id == m.referee_id).scalar() if m.referee_id else None),
            "referee_phone": m.referee_phone
        })
    return results

def export_tournament_data_to_excel(db: Session, tournament_id: int):
    # 1. Láº¥y thÃ´ng tin giáº£i Ä‘áº¥u
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="KhÃ´ng tÃ¬m tháº¥y giáº£i Ä‘áº¥u")

    # Táº¡o Workbook Excel má»›i
    wb = Workbook()
    
    # SHEET 1: DANH SÃCH Váº¬N Äá»˜NG VIÃŠN ÄÄ‚NG KÃ
    ws_players = wb.active
    ws_players.title = "Danh sÃ¡ch VÄV"
    
    # Style cho tiÃªu Ä‘á»
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center")

    headers = ["STT", "Há» TÃªn", "Sá»‘ Ä‘iá»‡n thoáº¡i", "Email", "TrÃ¬nh Ä‘á»™", "Tráº¡ng thÃ¡i", "Thanh toÃ¡n"]
    ws_players.append(headers)
    
    for col in range(1, len(headers) + 1):
        cell = ws_players.cell(row=1, column=col)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align

    # Set Ä‘á»™ rá»™ng cá»™t
    ws_players.column_dimensions['B'].width = 25
    ws_players.column_dimensions['C'].width = 15
    ws_players.column_dimensions['D'].width = 25
    ws_players.column_dimensions['E'].width = 15
    ws_players.column_dimensions['F'].width = 15
    ws_players.column_dimensions['G'].width = 15

    # Láº¥y dá»¯ liá»‡u VÄV
    regs = db.query(Registration, Player, User).join(
        Player, Registration.player_id == Player.id
    ).join(
        User, Player.user_id == User.id
    ).filter(
        Registration.tournament_id == tournament_id,
        Registration.deleted_at.is_(None)
    ).all()

    for idx, (reg, player, user) in enumerate(regs, start=1):
        ws_players.append([
            idx,
            user.full_name,
            user.phone,
            user.email,
            player.skill_level or "N/A",
            "ÄÃ£ Check-in" if reg.status == "checked_in" else "ÄÃ£ duyá»‡t" if reg.status == "confirmed" else "Chá» duyá»‡t",
            "ÄÃ£ thanh toÃ¡n" if reg.payment_status == "paid" else "ChÆ°a thanh toÃ¡n"
        ])

    # SHEET 2: Káº¾T QUáº¢ TRáº¬N Äáº¤U (BRACKET)

    ws_matches = wb.create_sheet(title="Káº¿t quáº£ Thi Ä‘áº¥u")
    matches_headers = ["Tráº­n sá»‘", "VÃ²ng Ä‘áº¥u", "VÄV A", "VÄV B", "Tá»· sá»‘", "NgÆ°á»i tháº¯ng", "Tráº¡ng thÃ¡i"]
    ws_matches.append(matches_headers)

    for col in range(1, len(matches_headers) + 1):
        cell = ws_matches.cell(row=1, column=col)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align

    ws_matches.column_dimensions['C'].width = 25
    ws_matches.column_dimensions['D'].width = 25
    ws_matches.column_dimensions['E'].width = 20
    ws_matches.column_dimensions['F'].width = 25

    # Láº¥y dá»¯ liá»‡u Match
    matches = db.query(Match).filter(Match.tournament_id == tournament_id).order_by(Match.match_no).all()
    
    def get_player_name(reg_id):
        if not reg_id: return "Chá» xáº¿p nhÃ¡nh"
        r = db.query(Registration).filter(Registration.id == reg_id).first()
        if not r: return "N/A"
        u = db.query(User).join(Player).filter(Player.id == r.player_id).first()
        if not u: return "VÄV"
        return f"{u.full_name} - {r.partner_name}" if r.partner_name else u.full_name

    for m in matches:
        p1_name = get_player_name(m.side_a_registration_id)
        p2_name = get_player_name(m.side_b_registration_id)
        
        winner_name = ""
        if m.status == "completed":
            winner_name = p1_name if m.winner_side == "side_a" else p2_name

        ws_matches.append([
            m.match_no,
            m.round_code,
            p1_name,
            p2_name,
            m.result_note or "-",
            winner_name,
            "ÄÃ£ xong" if m.status == "completed" else "ChÆ°a Ä‘áº¥u"
        ])

    # LÆ°u vÃ o bá»™ nhá»› táº¡m (BytesIO) Ä‘á»ƒ gá»­i tháº³ng vá» Frontend mÃ  khÃ´ng cáº§n lÆ°u rÃ¡c trong á»• cá»©ng mÃ¡y chá»§
    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)
    
    # Tráº£ vá» file stream vÃ  tÃªn file an toÃ n
    safe_name = "".join([c if c.isalnum() else "_" for c in tournament.name])
    file_name = f"BaoCao_{safe_name}.xlsx"
    
    return stream, file_name

def get_tournament_and_valid_emails(db: Session, tournament_id: int):
    # Láº¥y thÃ´ng tin giáº£i Ä‘áº¥u
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        return None, []

    # Láº¥y danh sÃ¡ch email há»£p lá»‡
    valid_regs = db.query(User.email).join(
        Player, User.id == Player.user_id
    ).join(
        Registration, Player.id == Registration.player_id
    ).filter(
        Registration.tournament_id == tournament_id, 
        Registration.deleted_at.is_(None)
    ).all()
    
    # Lá»c bá» cÃ¡c pháº§n tá»­ rá»—ng
    bcc_emails = [reg[0] for reg in valid_regs if reg[0]]
    
    return tournament, bcc_emails

def save_mail_campaign(
    db: Session, 
    tournament_id: int, 
    subject: str, 
    message: str, 
    total_recipients: int,
    scheduled_at = None,   # <--- ThÃªm dÃ²ng nÃ y
    status: str = "pending" # <--- ThÃªm dÃ²ng nÃ y
):
    new_campaign = MailCampaign(
        tournament_id=tournament_id,
        subject=subject,
        message=message,
        total_recipients=total_recipients,
        scheduled_at=scheduled_at, # <--- LÆ°u vÃ o DB
        status=status              # <--- LÆ°u vÃ o DB
    )
    db.add(new_campaign)
    db.commit()
    db.refresh(new_campaign)
    return new_campaign

def generate_round_robin_draw(db: Session, tournament_id: int, category_id: int, num_groups: int = 1, draw_size: Optional[int] = None):
    """Generate round-robin group matches.

    When draw_size is provided, it is treated as the number of teams/pairs in
    the same manual setup style as knockout. Missing registrations are kept as
    empty slots so admins can assign them later.
    """
    if num_groups < 1:
        num_groups = 1

    query = db.query(Registration).filter(
        Registration.tournament_id == tournament_id,
        Registration.status.in_(["pending", "approved", "confirmed", "paid", "checked_in"]),
        Registration.deleted_at.is_(None)
    )
    if category_id:
        query = query.filter(Registration.tournament_category_id == category_id)
    players = query.all()

    participant_count = draw_size if draw_size and draw_size > 0 else len(players)
    if participant_count < 2:
        raise HTTPException(status_code=400, detail="Khong du so doi de tao lich thi dau vong tron.")

    match_del_query = db.query(Match).filter(
        Match.tournament_id == tournament_id,
        Match.stage_type == "group_stage"
    )
    if category_id:
        match_del_query = match_del_query.filter(Match.tournament_category_id == category_id)
    match_del_query.delete()
    db.flush()

    # Manual setup mode: round-robin only creates empty match frames.
    # Admins assign players/pairs later from the draw management screen.
    slots = [{"registration": None, "is_bye": False} for _ in range(participant_count)]

    groups = [slots[i::num_groups] for i in range(num_groups)]

    match_no = 1
    for group_idx, group_players in enumerate(groups):
        group_id = group_idx + 1
        n = len(group_players)

        if n % 2 != 0:
            group_players.append({"registration": None, "is_bye": True})
            n += 1

        for round_num in range(n - 1):
            for i in range(n // 2):
                p1 = group_players[i]
                p2 = group_players[n - 1 - i]

                if p1.get("is_bye") or p2.get("is_bye"):
                    continue

                reg_a = p1.get("registration")
                reg_b = p2.get("registration")
                new_match = Match(
                    tournament_id=tournament_id,
                    tournament_category_id=category_id,
                    stage_type="group_stage",
                    group_id=group_id,
                    round_code=f"G{group_id}-R{round_num + 1}",
                    match_no=match_no,
                    side_a_registration_id=reg_a.id if reg_a else None,
                    side_b_registration_id=reg_b.id if reg_b else None,
                    status="pending",
                    best_of_sets=3,
                    elo_affected=True
                )
                db.add(new_match)
                match_no += 1

            group_players.insert(1, group_players.pop())

    db.commit()
    return {
        "message": "Da tao lich thi dau vong tron thanh cong.",
        "total_slots": participant_count,
        "num_groups": num_groups,
        "matches_created": match_no - 1
    }

def calculate_tournament_standings(db: Session, tournament_id: int, category_id: Optional[int] = None):
    """HÃ m lÃµi tÃ­nh Ä‘iá»ƒm (DÃ¹ng cho cáº£ VÃ²ng trÃ²n vÃ  Xáº¿p háº¡ng tá»•ng thá»ƒ)"""
    # 1. Thá»­ láº¥y cÃ¡c tráº­n vÃ²ng báº£ng trÆ°á»›c
    query = db.query(Match).filter(
        Match.tournament_id == tournament_id,
        Match.stage_type == "group_stage",
        Match.status == "completed" 
    )
    if category_id:
        query = query.filter(Match.tournament_category_id == category_id)
    
    matches = query.all()

    # 2. Náº¿u khÃ´ng cÃ³ tráº­n vÃ²ng báº£ng nÃ o, láº¥y táº¥t cáº£ cÃ¡c tráº­n Ä‘Ã£ xong cá»§a giáº£i (cho Knockout/Playoff)
    if not matches:
        query = db.query(Match).filter(
            Match.tournament_id == tournament_id,
            Match.status == "completed"
        )
        if category_id:
            query = query.filter(Match.tournament_category_id == category_id)
        matches = query.all()

    standings = {}

    def safe_int(val):
        return int(val) if val is not None else 0

    for match in matches:
        # XÃ¡c Ä‘á»‹nh tÃªn báº£ng
        if match.stage_type == "group_stage" and match.group_id:
            group = f"Báº£ng {match.group_id}"
        else:
            group = "Xáº¿p háº¡ng tá»•ng thá»ƒ"

        if group not in standings:
            standings[group] = {}

        p1_id = match.side_a_registration_id
        p2_id = match.side_b_registration_id

        if not p1_id or not p2_id:
            continue

        for p_id in [p1_id, p2_id]:
            if p_id not in standings[group]:
                user_record = db.query(
                    User.full_name, 
                    User.avatar_url,
                    Registration.partner_name, 
                    Registration.partner_player_id, 
                    Registration.partner_user_id,
                    Registration.player_id, 
                    User.id
                ).join(
                    Player, User.id == Player.user_id
                ).join(
                    Registration, Player.id == Registration.player_id
                ).filter(
                    Registration.id == p_id
                ).first()
                
                player_name = user_record[0] if user_record else "Unknown"
                player_avatar = user_record[1] if user_record else None
                partner_name = user_record[2] if user_record else None
                partner_player_id = user_record[3] if user_record else None
                partner_user_id_reg = user_record[4] if user_record else None
                player_user_id = user_record[6] if user_record else None
                
                # Náº¿u cÃ³ mapping ID Ä‘á»“ng Ä‘á»™i, láº¥y User ID cá»§a Ä‘á»“ng Ä‘á»™i
                partner_user_id = partner_user_id_reg
                partner_avatar = None
                
                if partner_user_id:
                    p_user = db.query(User).filter(User.id == partner_user_id).first()
                    if p_user:
                        partner_name = p_user.full_name
                        partner_avatar = p_user.avatar_url
                elif partner_player_id:
                    p_user = db.query(User).join(Player).filter(Player.id == partner_player_id).first()
                    if p_user:
                        partner_name = p_user.full_name
                        partner_user_id = p_user.id
                        partner_avatar = p_user.avatar_url
                    
                standings[group][p_id] = {
                    "player_name": player_name, 
                    "player_avatar": player_avatar,
                    "player_id": player_user_id,
                    "partner_name": partner_name,
                    "partner_avatar": partner_avatar,
                    "partner_player_id": partner_user_id,
                    "played": 0, "won": 0, "lost": 0, "points": 0,
                    "sets_won": 0, "sets_lost": 0, 
                    "games_won": 0, "games_lost": 0
                }

        p1_games = safe_int(match.set1_a) + safe_int(match.set2_a) + safe_int(match.set3_a)
        p2_games = safe_int(match.set1_b) + safe_int(match.set2_b) + safe_int(match.set3_b)

        p1_sets = 0
        p2_sets = 0
        if safe_int(match.set1_a) > safe_int(match.set1_b): p1_sets += 1
        elif safe_int(match.set1_b) > safe_int(match.set1_a): p2_sets += 1
        if safe_int(match.set2_a) > safe_int(match.set2_b): p1_sets += 1
        elif safe_int(match.set2_b) > safe_int(match.set2_a): p2_sets += 1
        if safe_int(match.set3_a) > safe_int(match.set3_b): p1_sets += 1
        elif safe_int(match.set3_b) > safe_int(match.set3_a): p2_sets += 1

        is_p1_winner = match.winner_registration_id == p1_id
        standings[group][p1_id]["played"] += 1
        standings[group][p1_id]["won"] += 1 if is_p1_winner else 0
        standings[group][p1_id]["lost"] += 0 if is_p1_winner else 1
        standings[group][p1_id]["points"] += 3 if is_p1_winner else 0
        standings[group][p1_id]["sets_won"] += p1_sets
        standings[group][p1_id]["sets_lost"] += p2_sets
        standings[group][p1_id]["games_won"] += p1_games
        standings[group][p1_id]["games_lost"] += p2_games

        is_p2_winner = match.winner_registration_id == p2_id
        standings[group][p2_id]["played"] += 1
        standings[group][p2_id]["won"] += 1 if is_p2_winner else 0
        standings[group][p2_id]["lost"] += 0 if is_p2_winner else 1
        standings[group][p2_id]["points"] += 3 if is_p2_winner else 0
        standings[group][p2_id]["sets_won"] += p2_sets
        standings[group][p2_id]["sets_lost"] += p1_sets
        standings[group][p2_id]["games_won"] += p2_games
        standings[group][p2_id]["games_lost"] += p1_games

    result = []
    for group_name, players in standings.items():
        for p_id, stats in players.items():
            stats["set_diff"] = stats["sets_won"] - stats["sets_lost"]
            stats["game_diff"] = stats["games_won"] - stats["games_lost"]

        sorted_players = sorted(
            players.items(), 
            key=lambda x: (x[1]['points'], x[1]['set_diff'], x[1]['game_diff']), 
            reverse=True
        )
        
        result.append({
            "group_name": group_name,
            "rankings": [{"registration_id": k, **v} for k, v in sorted_players]
        })

    return result

def generate_playoff_draw(db: Session, tournament_id: int, category_id: int, advancers_per_group: int = 2):
    """Finalize group standings and create a knockout playoff tree."""
    if advancers_per_group < 1:
        raise ValueError("So VDV di tiep moi bang phai lon hon 0.")

    all_group_rows = db.query(Match.group_id).filter(
        Match.tournament_id == tournament_id,
        Match.tournament_category_id == category_id,
        Match.stage_type == "group_stage",
        Match.group_id.isnot(None)
    ).distinct().all()
    expected_group_ids = sorted(int(row[0]) for row in all_group_rows if row[0] is not None)

    if not expected_group_ids:
        raise ValueError("Chua co bang dau nao de chot Playoff.")

    group_matches_query = db.query(Match).filter(
        Match.tournament_id == tournament_id,
        Match.tournament_category_id == category_id,
        Match.stage_type == "group_stage",
        or_(
            Match.status == "completed",
            Match.winner_registration_id.isnot(None)
        ),
        Match.group_id.isnot(None)
    )
    group_matches = group_matches_query.order_by(Match.group_id.asc(), Match.round_code.asc(), Match.match_no.asc()).all()

    if not group_matches:
        raise ValueError("Chua co tran vong bang nao hoan thanh. Vui long cap nhat ty so.")

    grouped_stats = {}

    def safe_int(val):
        return int(val) if val is not None else 0

    def ensure_stat(group_id: int, registration_id: int):
        if group_id not in grouped_stats:
            grouped_stats[group_id] = {}
        if registration_id not in grouped_stats[group_id]:
            grouped_stats[group_id][registration_id] = {
                "registration_id": registration_id,
                "played": 0,
                "won": 0,
                "lost": 0,
                "points": 0,
                "sets_won": 0,
                "sets_lost": 0,
                "games_won": 0,
                "games_lost": 0,
            }
        return grouped_stats[group_id][registration_id]

    for match in group_matches:
        if not match.side_a_registration_id or not match.side_b_registration_id or not match.winner_registration_id:
            continue

        group_id = int(match.group_id)
        side_a = ensure_stat(group_id, match.side_a_registration_id)
        side_b = ensure_stat(group_id, match.side_b_registration_id)

        a_games = safe_int(match.set1_a) + safe_int(match.set2_a) + safe_int(match.set3_a)
        b_games = safe_int(match.set1_b) + safe_int(match.set2_b) + safe_int(match.set3_b)

        a_sets = 0
        b_sets = 0
        for a_score, b_score in [
            (match.set1_a, match.set1_b),
            (match.set2_a, match.set2_b),
            (match.set3_a, match.set3_b),
        ]:
            a_score = safe_int(a_score)
            b_score = safe_int(b_score)
            if a_score > b_score:
                a_sets += 1
            elif b_score > a_score:
                b_sets += 1

        a_won = match.winner_registration_id == match.side_a_registration_id
        b_won = match.winner_registration_id == match.side_b_registration_id

        side_a["played"] += 1
        side_a["won"] += 1 if a_won else 0
        side_a["lost"] += 0 if a_won else 1
        side_a["points"] += 3 if a_won else 0
        side_a["sets_won"] += a_sets
        side_a["sets_lost"] += b_sets
        side_a["games_won"] += a_games
        side_a["games_lost"] += b_games

        side_b["played"] += 1
        side_b["won"] += 1 if b_won else 0
        side_b["lost"] += 0 if b_won else 1
        side_b["points"] += 3 if b_won else 0
        side_b["sets_won"] += b_sets
        side_b["sets_lost"] += a_sets
        side_b["games_won"] += b_games
        side_b["games_lost"] += a_games

    group_tops = []
    insufficient_groups = []
    for group_id in expected_group_ids:
        players = list(grouped_stats.get(group_id, {}).values())
        for player in players:
            player["set_diff"] = player["sets_won"] - player["sets_lost"]
            player["game_diff"] = player["games_won"] - player["games_lost"]

        ranked_players = sorted(
            players,
            key=lambda item: (item["points"], item["set_diff"], item["game_diff"], item["games_won"]),
            reverse=True
        )
        top_players = ranked_players[:advancers_per_group]
        if len(top_players) < advancers_per_group:
            insufficient_groups.append(f"Bang {group_id}: co {len(top_players)}/{advancers_per_group}")
        group_tops.append(top_players)

    if insufficient_groups:
        raise ValueError("Mot so bang chua du VDV/cap co diem de chot Playoff: " + "; ".join(insufficient_groups))

    seeded_players = []
    for rank_index in range(advancers_per_group):
        for group in group_tops:
            if rank_index < len(group):
                seeded_players.append(group[rank_index])

    participant_count = len(seeded_players)
    if participant_count < 2:
        raise ValueError("Can it nhat 2 VDV/cap dau de tao Playoff.")

    db.query(Match).filter(
        Match.tournament_id == tournament_id,
        Match.tournament_category_id == category_id,
        Match.stage_type == "playoff"
    ).delete()
    db.flush()

    round_match_counts = []
    current_participants = participant_count
    while current_participants > 1:
        current_matches = math.ceil(current_participants / 2)
        round_match_counts.append(current_matches)
        current_participants = current_matches

    label_by_match_count = {
        16: "1/16",
        8: "1/8",
        4: "1/4",
        2: "1/2",
        1: "FINAL"
    }

    matches_by_round = {}
    for round_index, num_matches in enumerate(round_match_counts):
        matches_by_round[round_index] = []
        round_code = label_by_match_count.get(num_matches, f"R{num_matches * 2}")
        for idx in range(num_matches):
            new_match = Match(
                tournament_id=tournament_id,
                tournament_category_id=category_id,
                stage_type="playoff",
                round_code=round_code,
                match_no=idx + 1,
                status="pending",
                best_of_sets=3,
                elo_affected=True
            )
            db.add(new_match)
            matches_by_round[round_index].append(new_match)

    db.flush()

    incoming_counts = {}
    for round_index in range(0, len(round_match_counts) - 1):
        for match in matches_by_round[round_index]:
            for future_match in matches_by_round[round_index + 1]:
                current_incoming = incoming_counts.get(future_match.id, 0)
                if current_incoming < 2:
                    match.next_match_id = future_match.id
                    incoming_counts[future_match.id] = current_incoming + 1
                    break

    first_round_slots = seeded_players[:]
    target_slot_count = round_match_counts[0] * 2
    while len(first_round_slots) < target_slot_count:
        first_round_slots.append(None)

    first_round_pairs = []
    for index in range(round_match_counts[0]):
        first_round_pairs.append((first_round_slots[index], first_round_slots[target_slot_count - 1 - index]))

    for match, pair in zip(matches_by_round[0], first_round_pairs):
        side_a, side_b = pair
        match.side_a_registration_id = side_a["registration_id"] if side_a else None
        match.side_b_registration_id = side_b["registration_id"] if side_b else None

    db.commit()
    return {
        "message": "Da chot vong bang va tao so do Playoff thanh cong.",
        "qualified_count": participant_count,
        "first_round_matches": round_match_counts[0],
        "rounds": len(round_match_counts)
    }

def auto_update_tournament_statuses(db: Session):
    """HÃ m cháº¡y ngáº§m Ä‘á»ƒ quÃ©t vÃ  cáº­p nháº­t tráº¡ng thÃ¡i giáº£i Ä‘áº¥u dá»±a trÃªn thá»i gian thá»±c táº¿."""
    today = datetime.utcnow().date()
    
    # 1. Chuyá»ƒn tá»« 'open' sang 'ongoing' náº¿u Ä‘Ã£ Ä‘áº¿n ngÃ y khai máº¡c
    open_tours = db.query(Tournament).filter(
        Tournament.status == "open",
        Tournament.start_date <= today
    ).all()
    for tour in open_tours:
        tour.status = "ongoing"
        
    # 2. Chuyá»ƒn sang 'finished' náº¿u quÃ¡ ngÃ y káº¿t thÃºc
    # Chá»‰ quÃ©t cÃ¡c giáº£i Ä‘ang má»Ÿ hoáº·c Ä‘ang diá»…n ra mÃ  Ä‘Ã£ quÃ¡ háº¡n
    past_tours = db.query(Tournament).filter(
        Tournament.status.in_(["open", "ongoing"]),
        Tournament.end_date < today
    ).all()
    for tour in past_tours:
        tour.status = "finished"
        
    db.commit()
    return len(open_tours) + len(past_tours)
