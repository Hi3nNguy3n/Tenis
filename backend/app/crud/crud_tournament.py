# backend/app/crud/crud_tournament.py
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List, Dict, Any
from sqlalchemy import func, desc, or_
from fastapi import HTTPException
from datetime import datetime
import math
import random

from app.models.models import Tournament, Match, Registration, Player, User, Payment, Court, MailCampaign, TournamentCategory
from app.schemas.tournament_schemas import TournamentCreate, TournamentUpdate, MatchScoreUpdate, MatchScheduleUpdate, GenerateDrawRequest
from app.core.audit import log_action

import io
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

def create_tournament(db: Session, tournament: TournamentCreate):
    # 1. KIỂM TRA TRÙNG SLUG TRƯỚC KHI LƯU
    existing_slug = db.query(Tournament).filter(Tournament.slug == tournament.slug).first()
    if existing_slug:
        # Nếu trùng, trả về lỗi 400 (Bad Request) thay vì để DB sập (500)
        raise HTTPException(
            status_code=400, 
            detail="Đường dẫn (Slug) này đã được sử dụng cho một giải đấu khác. Vui lòng chọn đường dẫn khác!"
        )

    # 2. NẾU KHÔNG TRÙNG THÌ MỚI CHO TẠO
    db_tournament = Tournament(**tournament.model_dump())
    db.add(db_tournament)
    db.commit()
    db.refresh(db_tournament)

    # 3. TỰ ĐỘNG TẠO 1 CATEGORY MẶC ĐỊNH (Để dropdown không bị trống và hỗ trợ đa nội dung)
    # Map sang Tiếng Việt cho thân thiện
    gender_map = {"men": "Nam", "women": "Nữ", "mixed": "Nam Nữ"}
    type_map = {"singles": "Đơn", "doubles": "Đôi"}
    
    gender_vn = gender_map.get(db_tournament.gender_division.lower(), db_tournament.gender_division)
    type_vn = type_map.get(db_tournament.category_type.lower(), db_tournament.category_type)
    
    # Tên nội dung gọn gàng: "Đôi Nam Nữ", "Đơn Nam"...
    category_name = f"{type_vn} {gender_vn}"
    if db_tournament.gender_division.lower() == "mixed":
        category_name = "Đôi Nam Nữ" # Đặc biệt cho Mixed Doubles

    default_category = TournamentCategory(
        tournament_id=db_tournament.id,
        name=category_name,
        category_type=f"{db_tournament.gender_division.lower()}_{db_tournament.category_type.lower()}",
        max_participants=db_tournament.draw_size,
        max_points=None
    )
    db.add(default_category)
    db.commit()
    
    db.refresh(db_tournament)
    return db_tournament

def delete_tournament_db(db: Session, tournament_id: int):
    """Xóa toàn bộ giải đấu và các dữ liệu liên quan (Cascade manual)"""
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Không tìm thấy giải đấu để xóa.")

    # 1. Xóa các trận đấu liên quan
    db.query(Match).filter(Match.tournament_id == tournament_id).delete()
    
    # 2. Xóa các lượt đăng ký
    db.query(Registration).filter(Registration.tournament_id == tournament_id).delete()
    
    # 3. Xóa các nội dung thi đấu
    db.query(TournamentCategory).filter(TournamentCategory.tournament_id == tournament_id).delete()
    
    # 4. Xóa các chiến dịch email
    db.query(MailCampaign).filter(MailCampaign.tournament_id == tournament_id).delete()

    # 5. Cuối cùng mới xóa giải đấu
    db.delete(tournament)
    db.commit()
    return {"message": "Đã xóa giải đấu thành công!", "id": tournament_id}


def get_tournaments_with_counts(db: Session, skip: int = 0, limit: int = 10, status: str = None):
    query = db.query(Tournament).options(joinedload(Tournament.categories))
    if status:
        query = query.filter(Tournament.status == status)
    
    tournaments = query.offset(skip).limit(limit).all()
    
    # Tính số slot đã đăng ký cho từng giải
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
        raise HTTPException(status_code=404, detail="Không tìm thấy giải đấu")
    
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
        raise HTTPException(status_code=404, detail="Không tìm thấy giải đấu")

    today = datetime.utcnow().date()
    if tournament_in.start_date and tournament_in.start_date < today:
        raise HTTPException(status_code=400, detail="Ngày khai mạc không được nằm trong quá khứ.")
    if tournament_in.end_date and tournament_in.start_date and tournament_in.end_date < tournament_in.start_date:
        raise HTTPException(status_code=400, detail="Ngày kết thúc phải sau ngày khai mạc.")

    for var, value in vars(tournament_in).items():
        setattr(db_tour, var, value)
        
    db.commit()
    db.refresh(db_tour)
    
    log_action(db, admin_id, "TOURNAMENT", "UPDATE", "Tournament", db_tour.id, None, {"name": db_tour.name}, "Cập nhật giải đấu")
    return db_tour

def generate_knockout_draw(db: Session, tournament_id: int, category_id: Optional[int] = None):
    query = db.query(Registration).filter(
        Registration.tournament_id == tournament_id,
        Registration.status.in_(["confirmed", "checked_in"]),
        Registration.deleted_at.is_(None)
    )
    if category_id:
        query = query.filter(Registration.tournament_category_id == category_id)
    regs = query.all()

    if not regs:
        raise HTTPException(status_code=400, detail="Chưa có vận động viên nào được duyệt tham gia để tạo nhánh đấu.")
    
    random.shuffle(regs)
    count = len(regs)
    rounds_needed = math.ceil(math.log2(count))
    if rounds_needed == 0: rounds_needed = 1
    total_slots = 2 ** rounds_needed 

    round_labels = {1: "FINAL", 2: "SF", 4: "QF", 8: "R16", 16: "R32", 32: "R64", 64: "R128"}

    match_del_query = db.query(Match).filter(Match.tournament_id == tournament_id, Match.stage_type == "knockout")
    if category_id:
        match_del_query = match_del_query.filter(Match.tournament_category_id == category_id)
    match_del_query.delete()
    db.flush()

    matches_by_round = {}
    for r in range(1, rounds_needed + 1):
        matches_by_round[r] = []
        num_matches = 2 ** (r - 1)
        label = round_labels.get(num_matches, f"R{num_matches*2}")

        for i in range(num_matches):
            m = Match(
                tournament_id=tournament_id, 
                tournament_category_id=category_id,
                stage_type="knockout", 
                round_code=label,
                match_no=i + 1, status="pending", best_of_sets=3, elo_affected=True
            )
            db.add(m)
            matches_by_round[r].append(m)

    db.flush() 

    for r in range(rounds_needed, 1, -1):
        current_round = matches_by_round[r]
        next_round = matches_by_round[r - 1]
        for i in range(len(current_round)):
            parent_match_index = i // 2 
            current_round[i].next_match_id = next_round[parent_match_index].id

    first_round_matches = matches_by_round[rounds_needed]
    slots = [None] * total_slots
    for i in range(count):
        slots[i] = regs[i]

    slot_idx = 0
    for m in first_round_matches:
        reg_a = slots[slot_idx]
        reg_b = slots[slot_idx + 1]
        slot_idx += 2

        m.side_a_registration_id = reg_a.id if reg_a else None
        m.side_b_registration_id = reg_b.id if reg_b else None

        if reg_a and not reg_b:
            m.status = "completed"
            m.winner_side = "side_a"
            m.winner_registration_id = reg_a.id
            m.result_note = "BYE"
        elif not reg_a and reg_b:
            m.status = "completed"
            m.winner_side = "side_b"
            m.winner_registration_id = reg_b.id
            m.result_note = "BYE"

    db.commit()

    for m in first_round_matches:
        if m.status == "completed" and m.next_match_id and m.winner_registration_id:
            next_m = db.query(Match).filter(Match.id == m.next_match_id).first()
            if next_m:
                if m.match_no % 2 != 0:
                    next_m.side_a_registration_id = m.winner_registration_id
                else:
                    next_m.side_b_registration_id = m.winner_registration_id
    db.commit()

    return {
        "message": "Tuyệt vời! Đã tạo xong sơ đồ thi đấu.", 
        "total_players": count,
        "rounds": rounds_needed
    }

def get_tournament_matches_detail(db: Session, tournament_id: int, category_id: Optional[int] = None):
    query = db.query(Match).filter(Match.tournament_id == tournament_id)
    if category_id:
        query = query.filter(Match.tournament_category_id == category_id)
    
    matches = query.order_by(Match.match_no).all()
    results = []
    for m in matches:
        p1_name = "Chưa xác định"
        p2_name = "Chưa xác định"
        p1_partner_name = None
        p2_partner_name = None
        
        reg_a = db.query(Registration).filter(Registration.id == m.side_a_registration_id).first() if m.side_a_registration_id else None
        if reg_a:
            user_a = db.query(User).join(Player).filter(Player.id == reg_a.player_id).first()
            if user_a:
                p1_name = user_a.full_name
            p1_partner_name = reg_a.partner_name

        reg_b = db.query(Registration).filter(Registration.id == m.side_b_registration_id).first() if m.side_b_registration_id else None
        if reg_b:
            user_b = db.query(User).join(Player).filter(Player.id == reg_b.player_id).first()
            if user_b:
                p2_name = user_b.full_name
            p2_partner_name = reg_b.partner_name
                
        results.append({
            "id": m.id, "round_code": m.round_code, "match_no": m.match_no,
            "p1_name": p1_name, "p2_name": p2_name,
            "p1_partner_name": p1_partner_name, "p2_partner_name": p2_partner_name,
            "status": m.status,
            "court_id": m.court_id, 
            "start_time": m.start_time.isoformat() if m.start_time else None, 
            "winner_side": m.winner_side,
            "referee_id": m.referee_id,
            "referee_name": m.referee_name,
            "referee_phone": m.referee_phone,
            "score_summary": getattr(m, 'score_summary', None) or getattr(m, 'result_note', None),
            "video_url": getattr(m, 'video_url', None),
            "image_url": getattr(m, 'image_url', None),
            "tournament_category_id": m.tournament_category_id
        })
    return results

def schedule_match_db(db: Session, match_id: int, payload: MatchScheduleUpdate):
    db_match = db.query(Match).filter(Match.id == match_id).first()
    if not db_match:
        raise HTTPException(status_code=404, detail="Không tìm thấy trận đấu")
    
    tournament = db.query(Tournament).filter(Tournament.id == db_match.tournament_id).first()
    if tournament:
        schedule_date = payload.start_time.date()
        if tournament.start_date and schedule_date < tournament.start_date:
            raise HTTPException(status_code=400, detail=f"Giải đấu bắt đầu từ ngày {tournament.start_date.strftime('%d/%m/%Y')}.")
        if tournament.end_date and schedule_date > tournament.end_date:
            raise HTTPException(status_code=400, detail=f"Giải đấu kết thúc vào ngày {tournament.end_date.strftime('%d/%m/%Y')}.")
            
    db_match.court_id = payload.court_id
    db_match.start_time = payload.start_time
    if payload.referee_id:
        db_match.referee_id = payload.referee_id
    db_match.referee_name = payload.referee_name
    db_match.referee_phone = payload.referee_phone
    db.commit()
    return {"message": "Đã cập nhật lịch thi đấu"}

def get_all_matches_detail(db: Session):
    matches = db.query(Match, Tournament, Court).join(
        Tournament, Match.tournament_id == Tournament.id
    ).outerjoin(
        Court, Match.court_id == Court.id
    ).order_by(desc(Match.start_time)).all()

    # Helper lấy tên VĐV từ registration_id
    def get_player_name(reg_id):
        if not reg_id:
            return None
        reg = db.query(Registration).filter(Registration.id == reg_id).first()
        if not reg:
            return None
        user = db.query(User).join(Player, Player.user_id == User.id).filter(Player.id == reg.player_id).first()
        if not user:
            return None
        return f"{user.full_name} - {reg.partner_name}" if reg.partner_name else user.full_name

    results = []
    for m, t, c in matches:
        # Ưu tiên match_date của trận, fallback về start_time.date(), cuối cùng là start_date giải
        if m.match_date:
            match_date = m.match_date
        elif m.start_time:
            match_date = m.start_time.date()
        else:
            match_date = t.start_date

        results.append({
            "id": m.id,
            "tournament_id": t.id,
            "tournament": t.name,
            "tournament_start_date": t.start_date.isoformat() if t.start_date else None,
            "tournament_end_date": t.end_date.isoformat() if t.end_date else None,
            "location": t.location or "Vietnam",
            "round_code": m.round_code,
            "court": c.court_name if c else "Chưa gán sân",
            "date": match_date.isoformat() if match_date else None,
            "start_time": m.start_time.isoformat() if m.start_time else None,
            "start": m.start_time.strftime("%H:%M") if m.start_time else "--:--",
            "status": m.status,
            "p1_name": get_player_name(m.side_a_registration_id),
            "p2_name": get_player_name(m.side_b_registration_id),
            "winner_side": m.winner_side,
            "score": m.score_summary,
        })
    return results

def calculate_elo_and_update_match(db: Session, match_id: int, payload: MatchScoreUpdate):
    # 1. Tìm trận đấu và kiểm tra trạng thái
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match or match.status == "completed":
        raise HTTPException(status_code=400, detail="Trận đấu không tồn tại hoặc đã kết thúc.")

    # 0. Kiểm tra xem trận đấu có được phép tính ELO không
    if not getattr(match, 'elo_affected', False):
        # Nếu không tính ELO, chúng ta chỉ cập nhật trạng thái trận đấu
        match.status = "completed"
        match.score_summary = payload.score
        match.winner_side = payload.winner_side
        if payload.referee_id:
            match.referee_id = payload.referee_id
        match.referee_name = payload.referee_name
        match.referee_phone = payload.referee_phone
        db.commit()
        return {"message": "Cập nhật tỷ số thành công (Không tính ELO)"}

    # 1. LẤY PLAYER ID CỦA 2 BÊN
    p1_id = None
    p2_id = None

    if match.tournament_id:
        # Trường hợp trận đấu GIẢI: Lấy Player ID thông qua bảng Registration
        reg_a = db.query(Registration).filter(Registration.id == match.side_a_registration_id).first()
        reg_b = db.query(Registration).filter(Registration.id == match.side_b_registration_id).first()
        if reg_a: p1_id = reg_a.player_id
        if reg_b: p2_id = reg_b.player_id
        
        # Fallback: Nếu không tìm thấy qua Registration, lấy trực tiếp từ match (cho các trận tạo thủ công)
        if not p1_id: p1_id = match.player_a_id
        if not p2_id: p2_id = match.player_b_id
    else:
        # Trường hợp trận GIAO HỮU: Lấy trực tiếp từ player_a_id và player_b_id
        p1_id = match.player_a_id
        p2_id = match.player_b_id

    # 3. Kiểm tra tính đầy đủ của 2 vận động viên
    if not p1_id or not p2_id:
        raise HTTPException(status_code=400, detail="Trận đấu phải có đủ 2 VĐV mới tính được điểm Elo.")

    # 4. Xác định ai thắng ai thua dựa trên payload gửi lên
    win_p_id = p1_id if payload.winner_side == "side_a" else p2_id
    lose_p_id = p2_id if payload.winner_side == "side_a" else p1_id
    
    # Xác định registration_id của người thắng (chỉ dùng cho logic tiến vào vòng sau của Giải)
    win_reg_id = match.side_a_registration_id if payload.winner_side == "side_a" else match.side_b_registration_id

    winner_p = db.query(Player).filter(Player.id == win_p_id).first()
    loser_p = db.query(Player).filter(Player.id == lose_p_id).first()

    if not winner_p or not loser_p:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ vận động viên.")

    # 5. THUẬT TOÁN ELO
    K = 32
    Ra = winner_p.elo_points
    Rb = loser_p.elo_points
    E_winner = 1 / (1 + 10 ** ((Rb - Ra) / 400))
    elo_gain = round(K * (1 - E_winner))
    
    # Cập nhật chỉ số cho người thắng (và đồng đội nếu có)
    def update_p_stats(p, gain, is_win):
        p.elo_points += gain if is_win else -gain
        if is_win: p.wins += 1
        else: p.losses += 1
        p.matches_played += 1

    update_p_stats(winner_p, elo_gain, True)
    update_p_stats(loser_p, elo_gain, False)

    # Nếu là đánh đôi, cập nhật cho cả đồng đội
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

    # 6. Cập nhật thông tin trận đấu
    match.status = "completed"
    match.winner_side = payload.winner_side
    match.winner_registration_id = win_reg_id # Lưu reg_id nếu có
    match.result_note = payload.score
    if payload.video_url is not None:
        match.video_url = payload.video_url
    if payload.image_url is not None:
        match.image_url = payload.image_url
    if payload.referee_id:
        match.referee_id = payload.referee_id
    match.referee_name = payload.referee_name
    match.referee_phone = payload.referee_phone

    # 7. Xử lý logic thăng hạng nếu là trận đấu giải[cite: 33]
    message_suffix = ""
    if match.tournament_id:
        # Kiểm tra xem còn trận đấu nào chưa xong không
        remaining_matches = db.query(Match).filter(
            Match.tournament_id == match.tournament_id,
            Match.id != match.id, # Trừ trận hiện tại vừa xong
            Match.status.in_(["pending", "scheduled", "ongoing"])
        ).count()

        if remaining_matches == 0:
            tournament = db.query(Tournament).filter(Tournament.id == match.tournament_id).first()
            if tournament and tournament.status != "finished":
                tournament.status = "finished"
                # Cập nhật ID nhà vô địch nếu là trận Chung kết
                if match.round_code in ["FINAL", "F"] and hasattr(tournament, 'winner_player_id'):
                    tournament.winner_player_id = winner_p.id
                message_suffix = f" Giải đấu đã chính thức khép lại. Chúc mừng {winner_p.full_name if hasattr(winner_p, 'full_name') else winner_p.id}!"
        else:
            # Tự động đẩy người thắng vào trận đấu tiếp theo trong sơ đồ
            if match.next_match_id:
                next_m = db.query(Match).filter(Match.id == match.next_match_id).first()
                if next_m:
                    if match.match_no % 2 != 0:
                        next_m.side_a_registration_id = win_reg_id
                    else:
                        next_m.side_b_registration_id = win_reg_id

    db.commit()
    return {"message": f"Cập nhật kết quả thành công! {message_suffix}"}

def get_public_bracket_detail(db: Session, tournament_id: int, category_id: Optional[int] = None):
    query = db.query(Match).filter(Match.tournament_id == tournament_id)
    if category_id:
        query = query.filter(Match.tournament_category_id == category_id)
    matches = query.all()
    
    def get_player_data(reg_id):
        if not reg_id: return {"name": "Chưa xác định", "user_id": None, "partner_name": None, "partner_user_id": None}
        reg = db.query(Registration).filter(Registration.id == reg_id).first()
        if not reg: return {"name": "Chưa xác định", "user_id": None, "partner_name": None, "partner_user_id": None}
        
        user = db.query(User).join(Player).filter(Player.id == reg.player_id).first()
        data = {
            "name": user.full_name if user else "Chưa xác định",
            "user_id": user.id if user else None,
            "partner_name": None,
            "partner_user_id": None
        }
        
        if getattr(reg, "partner_player_id", None):
            partner_user = db.query(User).join(Player).filter(Player.id == reg.partner_player_id).first()
            if partner_user:
                data["partner_name"] = partner_user.full_name
                data["partner_user_id"] = partner_user.id
        elif reg.partner_name: # Thêm logic fallback lấy partner_name từ registration nếu không có partner_player_id
            data["partner_name"] = reg.partner_name
                
        return data

    results = []
    for m in matches:
        p1_data = get_player_data(m.side_a_registration_id)
        p2_data = get_player_data(m.side_b_registration_id)
        
        results.append({
            "id": m.id, "match_no": m.match_no, "round_code": m.round_code,
            "category_id": m.tournament_category_id,
            "p1_name": p1_data["name"],
            "p1_user_id": p1_data["user_id"],
            "p1_partner_name": p1_data["partner_name"],
            "p1_partner_user_id": p1_data["partner_user_id"],
            
            "p2_name": p2_data["name"],
            "p2_user_id": p2_data["user_id"],
            "p2_partner_name": p2_data["partner_name"],
            "p2_partner_user_id": p2_data["partner_user_id"],
            
            "winner_side": m.winner_side, "status": m.status,
            "start_time": m.start_time, "score": m.result_note,
            "video_url": getattr(m, "video_url", None),
            "image_url": getattr(m, "image_url", None),
            "referee_name": m.referee_name or (db.query(User.full_name).filter(User.id == m.referee_id).scalar() if m.referee_id else None),
            "referee_phone": m.referee_phone
        })
    return results

def export_tournament_data_to_excel(db: Session, tournament_id: int):
    # 1. Lấy thông tin giải đấu
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Không tìm thấy giải đấu")

    # Tạo Workbook Excel mới
    wb = Workbook()
    
    # SHEET 1: DANH SÁCH VẬN ĐỘNG VIÊN ĐĂNG KÝ
    ws_players = wb.active
    ws_players.title = "Danh sách VĐV"
    
    # Style cho tiêu đề
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center")

    headers = ["STT", "Họ Tên", "Số điện thoại", "Email", "Trình độ", "Trạng thái", "Thanh toán"]
    ws_players.append(headers)
    
    for col in range(1, len(headers) + 1):
        cell = ws_players.cell(row=1, column=col)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align

    # Set độ rộng cột
    ws_players.column_dimensions['B'].width = 25
    ws_players.column_dimensions['C'].width = 15
    ws_players.column_dimensions['D'].width = 25
    ws_players.column_dimensions['E'].width = 15
    ws_players.column_dimensions['F'].width = 15
    ws_players.column_dimensions['G'].width = 15

    # Lấy dữ liệu VĐV
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
            "Đã Check-in" if reg.status == "checked_in" else "Đã duyệt" if reg.status == "confirmed" else "Chờ duyệt",
            "Đã thanh toán" if reg.payment_status == "paid" else "Chưa thanh toán"
        ])

    # SHEET 2: KẾT QUẢ TRẬN ĐẤU (BRACKET)

    ws_matches = wb.create_sheet(title="Kết quả Thi đấu")
    matches_headers = ["Trận số", "Vòng đấu", "VĐV A", "VĐV B", "Tỷ số", "Người thắng", "Trạng thái"]
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

    # Lấy dữ liệu Match
    matches = db.query(Match).filter(Match.tournament_id == tournament_id).order_by(Match.match_no).all()
    
    def get_player_name(reg_id):
        if not reg_id: return "Chờ xếp nhánh"
        r = db.query(Registration).filter(Registration.id == reg_id).first()
        if not r: return "N/A"
        u = db.query(User).join(Player).filter(Player.id == r.player_id).first()
        if not u: return "VĐV"
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
            "Đã xong" if m.status == "completed" else "Chưa đấu"
        ])

    # Lưu vào bộ nhớ tạm (BytesIO) để gửi thẳng về Frontend mà không cần lưu rác trong ổ cứng máy chủ
    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)
    
    # Trả về file stream và tên file an toàn
    safe_name = "".join([c if c.isalnum() else "_" for c in tournament.name])
    file_name = f"BaoCao_{safe_name}.xlsx"
    
    return stream, file_name

def get_tournament_and_valid_emails(db: Session, tournament_id: int):
    # Lấy thông tin giải đấu
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        return None, []

    # Lấy danh sách email hợp lệ
    valid_regs = db.query(User.email).join(
        Player, User.id == Player.user_id
    ).join(
        Registration, Player.id == Registration.player_id
    ).filter(
        Registration.tournament_id == tournament_id, 
        Registration.deleted_at.is_(None)
    ).all()
    
    # Lọc bỏ các phần tử rỗng
    bcc_emails = [reg[0] for reg in valid_regs if reg[0]]
    
    return tournament, bcc_emails

def save_mail_campaign(
    db: Session, 
    tournament_id: int, 
    subject: str, 
    message: str, 
    total_recipients: int,
    scheduled_at = None,   # <--- Thêm dòng này
    status: str = "pending" # <--- Thêm dòng này
):
    new_campaign = MailCampaign(
        tournament_id=tournament_id,
        subject=subject,
        message=message,
        total_recipients=total_recipients,
        scheduled_at=scheduled_at, # <--- Lưu vào DB
        status=status              # <--- Lưu vào DB
    )
    db.add(new_campaign)
    db.commit()
    db.refresh(new_campaign)
    return new_campaign

def generate_round_robin_draw(db: Session, tournament_id: int, category_id: int, num_groups: int = 1):
    """Thuật toán chia bảng và tạo lịch thi đấu Vòng tròn cho từng nội dung"""
    
    # 1. Lấy danh sách VĐV đã xác nhận tham gia trong nội dung này
    players = db.query(Registration).filter(
        Registration.tournament_id == tournament_id,
        Registration.tournament_category_id == category_id,
        Registration.status == "confirmed",
        Registration.deleted_at.is_(None)
    ).all()

    if len(players) < 2:
        raise HTTPException(status_code=400, detail="Cần ít nhất 2 VĐV đã duyệt để tạo lịch thi đấu vòng tròn.")

    # 2. Xóa lịch thi đấu cũ của nội dung này (nếu có) để tạo lại
    db.query(Match).filter(
        Match.tournament_id == tournament_id,
        Match.tournament_category_id == category_id
    ).delete()
    
    # Đảo lộn ngẫu nhiên VĐV trước khi bốc thăm
    random.shuffle(players) 

    # 3. Chia đều VĐV vào các bảng
    # Mẹo Python: players[i::num_groups] sẽ chia đều mảng thành các phần bằng nhau
    groups = [players[i::num_groups] for i in range(num_groups)]
    
    match_no = 1
    for group_idx, group_players in enumerate(groups):
        group_id = group_idx + 1 # Đánh số bảng: 1 (A), 2 (B)...
        n = len(group_players)
        
        # Nếu số VĐV lẻ, thêm một "bóng ma" (None) đại diện cho việc được nghỉ (Bye) ở vòng đó
        if n % 2 != 0:
            group_players.append(None)
            n += 1
            
        # 4. Áp dụng thuật toán xoay vòng tạo trận
        for round_num in range(n - 1):
            for i in range(n // 2):
                p1 = group_players[i]
                p2 = group_players[n - 1 - i]
                
                # Nếu không ai đụng phải "bóng ma" thì tạo trận đấu
                if p1 is not None and p2 is not None:
                    new_match = Match(
                        tournament_id=tournament_id,
                        tournament_category_id=category_id,
                        stage_type="group_stage",
                        group_id=group_id, # Lưu ID bảng vào đây
                        round_code=f"G{group_id}-R{round_num+1}", # Mã vòng: Bảng 1 - Vòng 1
                        match_no=match_no,
                        side_a_registration_id=p1.id,
                        side_b_registration_id=p2.id,
                        status="scheduled",
                        best_of_sets=3 # Mặc định đánh 3 set
                    )
                    db.add(new_match)
                    match_no += 1
            
            # Xoay vòng danh sách: Rút người cuối cùng nhét vào vị trí số 1 (Giữ nguyên người số 0)
            group_players.insert(1, group_players.pop())

    db.commit()
    return {"message": f"Đã chia {num_groups} bảng và tạo lịch thi đấu vòng tròn thành công!"}

def calculate_tournament_standings(db: Session, tournament_id: int, category_id: Optional[int] = None):
    """Hàm lõi tính điểm (Dùng cho cả Vòng tròn và Xếp hạng tổng thể)"""
    # 1. Thử lấy các trận vòng bảng trước
    query = db.query(Match).filter(
        Match.tournament_id == tournament_id,
        Match.stage_type == "group_stage",
        Match.status == "completed" 
    )
    if category_id:
        query = query.filter(Match.tournament_category_id == category_id)
    
    matches = query.all()

    # 2. Nếu không có trận vòng bảng nào, lấy tất cả các trận đã xong của giải (cho Knockout/Playoff)
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
        # Xác định tên bảng
        if match.stage_type == "group_stage" and match.group_id:
            group = f"Bảng {match.group_id}"
        else:
            group = "Xếp hạng tổng thể"

        if group not in standings:
            standings[group] = {}

        p1_id = match.side_a_registration_id
        p2_id = match.side_b_registration_id

        if not p1_id or not p2_id:
            continue

        for p_id in [p1_id, p2_id]:
            if p_id not in standings[group]:
                user_record = db.query(User.full_name, Registration.partner_name, Registration.partner_player_id, Registration.player_id, User.id).join(
                    Player, User.id == Player.user_id
                ).join(
                    Registration, Player.id == Registration.player_id
                ).filter(
                    Registration.id == p_id
                ).first()
                
                player_name = user_record[0] if user_record else "Unknown"
                partner_name = user_record[1] if user_record else None
                partner_player_id = user_record[2] if user_record else None
                # QUAN TRỌNG: player_id ở đây trả về User ID để link profile
                player_id = user_record[4] if user_record else None
                
                # Nếu có mapping ID đồng đội, lấy User ID của đồng đội
                partner_user_id = None
                if partner_player_id:
                    p_user = db.query(User.full_name, User.id).join(Player).filter(Player.id == partner_player_id).first()
                    if p_user:
                        partner_name = p_user[0]
                        partner_user_id = p_user[1]
                    
                standings[group][p_id] = {
                    "player_name": player_name, 
                    "player_id": player_id,
                    "partner_name": partner_name,
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
    """Thuật toán tự động chốt vòng bảng và xếp cặp Playoff cho từng nội dung"""
    
    # 1. Gọi hàm cục bộ tính Bảng xếp hạng để lấy Top VĐV của nội dung này
    standings_data = calculate_tournament_standings(db=db, tournament_id=tournament_id, category_id=category_id)
    
    if not standings_data:
        raise ValueError("Chưa có trận vòng bảng nào hoàn thành. Vui lòng cập nhật tỷ số!")

    qualified_players = []
    num_groups = len(standings_data)

    # 2. Nhặt những người Top đầu của mỗi bảng ra
    for group in standings_data:
        top_players = group["rankings"][:advancers_per_group]
        qualified_players.append(top_players)

    match_pairs = []
    
    # 3. Thuật toán ghép cặp (Đã vá lỗi cho giải 3 người)
    if num_groups == 1:
        top_n = qualified_players[0]
        if len(top_n) < 2:
            raise ValueError("Bảng xếp hạng chưa đủ 2 người có điểm.")
            
        # NẾU CÓ 2 HOẶC 3 NGƯỜI: Lấy 2 người đứng đầu đánh Chung Kết
        if len(top_n) == 2 or len(top_n) == 3:
            match_pairs.append((top_n[0], top_n[1])) 
        # NẾU TỪ 4 NGƯỜI TRỞ LÊN: Bắt cặp Bán Kết (Nhất vs Tư, Nhì vs Ba)
        elif len(top_n) >= 4:
            match_pairs.append((top_n[0], top_n[3]))
            match_pairs.append((top_n[1], top_n[2]))
            
    elif num_groups == 2:
        group_a = qualified_players[0]
        group_b = qualified_players[1]
        
        if len(group_a) >= 2 and len(group_b) >= 2:
            match_pairs.append((group_a[0], group_b[1]))
            match_pairs.append((group_b[0], group_a[1]))
        else:
            raise ValueError("Mỗi bảng cần ít nhất 2 VĐV có điểm để thi đấu chéo.")

    if not match_pairs:
        raise ValueError("Không thể tạo Playoff với số lượng này. Vui lòng kiểm tra lại.")

    # 4. Ghi các trận Playoff vào Database cho nội dung này
    db.query(Match).filter(
        Match.tournament_id == tournament_id,
        Match.tournament_category_id == category_id,
        Match.stage_type == "playoff"
    ).delete()

    for idx, pair in enumerate(match_pairs):
        new_match = Match(
            tournament_id=tournament_id,
            tournament_category_id=category_id,
            stage_type="playoff",
            round_code="SF" if len(match_pairs) > 1 else "FINAL",
            match_no=idx + 1,
            side_a_registration_id=pair[0]["registration_id"],
            side_b_registration_id=pair[1]["registration_id"],
            status="scheduled",
            best_of_sets=3
        )
        db.add(new_match)

    db.commit()
    return {"message": f"Đã chốt sổ Vòng bảng và tạo {len(match_pairs)} trận Playoff thành công!"}

def auto_update_tournament_statuses(db: Session):
    """Hàm chạy ngầm để quét và cập nhật trạng thái giải đấu dựa trên thời gian thực tế."""
    today = datetime.utcnow().date()
    
    # 1. Chuyển từ 'open' sang 'ongoing' nếu đã đến ngày khai mạc
    open_tours = db.query(Tournament).filter(
        Tournament.status == "open",
        Tournament.start_date <= today
    ).all()
    for tour in open_tours:
        tour.status = "ongoing"
        
    # 2. Chuyển sang 'finished' nếu quá ngày kết thúc
    # Chỉ quét các giải đang mở hoặc đang diễn ra mà đã quá hạn
    past_tours = db.query(Tournament).filter(
        Tournament.status.in_(["open", "ongoing"]),
        Tournament.end_date < today
    ).all()
    for tour in past_tours:
        tour.status = "finished"
        
    db.commit()
    return len(open_tours) + len(past_tours)