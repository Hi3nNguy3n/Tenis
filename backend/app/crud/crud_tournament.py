# backend/app/crud/crud_tournament.py
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from fastapi import HTTPException
from datetime import datetime
import math
import random

from app.models.models import Tournament, Match, Registration, Player, User, Payment, Court
from app.schemas.tournament_schemas import TournamentCreate, TournamentUpdate
from app.core.audit import log_action

import io
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

def create_tournament(db: Session, tournament: TournamentCreate):
    db_tournament = Tournament(**tournament.model_dump())
    db.add(db_tournament)
    db.commit()
    db.refresh(db_tournament)
    return db_tournament

def get_tournaments_with_counts(db: Session, skip: int = 0, limit: int = 10, status: str = None):
    query = db.query(Tournament)
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
    t = db.query(Tournament).filter(Tournament.id == tournament_id).first()
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

def generate_knockout_draw(db: Session, tournament_id: int):
    regs = db.query(Registration).filter(
        Registration.tournament_id == tournament_id,
        Registration.status.in_(["confirmed", "checked_in"]),
        Registration.deleted_at.is_(None)
    ).all()

    if not regs:
        raise Exception("Không có vận động viên nào hợp lệ để tạo nhánh đấu.")

    random.shuffle(regs)
    count = len(regs)
    rounds_needed = math.ceil(math.log2(count))
    if rounds_needed == 0: rounds_needed = 1
    total_slots = 2 ** rounds_needed 

    round_labels = {1: "FINAL", 2: "SF", 4: "QF", 8: "R16", 16: "R32", 32: "R64", 64: "R128"}

    db.query(Match).filter(Match.tournament_id == tournament_id).delete()
    db.flush()

    matches_by_round = {}
    for r in range(1, rounds_needed + 1):
        matches_by_round[r] = []
        num_matches = 2 ** (r - 1)
        label = round_labels.get(num_matches, f"R{num_matches*2}")

        for i in range(num_matches):
            m = Match(
                tournament_id=tournament_id, stage_type="knockout", round_code=label,
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

def get_tournament_matches_detail(db: Session, tournament_id: int):
    matches = db.query(Match).filter(Match.tournament_id == tournament_id).order_by(Match.match_no).all()
    results = []
    for m in matches:
        p1_name = "Chưa xác định"
        p2_name = "Chưa xác định"
        
        if m.side_a_registration_id:
            reg_a = db.query(Registration).filter(Registration.id == m.side_a_registration_id).first()
            if reg_a:
                user = db.query(User).join(Player).filter(Player.id == reg_a.player_id).first()
                p1_name = user.full_name if user else "VĐV"
        
        if m.side_b_registration_id:
            reg_b = db.query(Registration).filter(Registration.id == m.side_b_registration_id).first()
            if reg_b:
                user = db.query(User).join(Player).filter(Player.id == reg_b.player_id).first()
                p2_name = user.full_name if user else "VĐV"
                
        results.append({
            "id": m.id, "round_code": m.round_code, "match_no": m.match_no,
            "p1_name": p1_name, "p2_name": p2_name, "status": m.status,
            "court_id": m.court_id, "start_time": m.start_time, "winner_side": m.winner_side
        })
    return results

def schedule_match_db(db: Session, match_id: int, payload):
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
    db.commit()
    return {"message": "Đã cập nhật lịch thi đấu"}

def get_all_matches_detail(db: Session):
    matches = db.query(Match, Tournament, Court).join(
        Tournament, Match.tournament_id == Tournament.id
    ).outerjoin(
        Court, Match.court_id == Court.id
    ).order_by(desc(Match.start_time)).all()
    
    results = []
    for m, t, c in matches:
        results.append({
            "id": m.id, "tournament": t.name, "court": c.court_name if c else "Chưa gán sân",
            "date": m.match_date or t.start_date,
            "start": m.start_time.strftime("%H:%M") if m.start_time else "--:--",
            "end": "--:--", "status": m.status
        })
    return results

def calculate_elo_and_update_match(db: Session, match_id: int, payload):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match or match.status == "completed":
        raise HTTPException(status_code=400, detail="Trận đấu không tồn tại hoặc đã kết thúc.")

    if payload.winner_side == "side_a":
        win_reg_id = match.side_a_registration_id
        lose_reg_id = match.side_b_registration_id
    else:
        win_reg_id = match.side_b_registration_id
        lose_reg_id = match.side_a_registration_id

    if not win_reg_id or not lose_reg_id:
        raise HTTPException(status_code=400, detail="Trận đấu phải có đủ 2 VĐV mới tính được điểm Elo.")

    def get_player_by_reg(reg_id):
        reg = db.query(Registration).filter(Registration.id == reg_id).first()
        return db.query(Player).filter(Player.id == reg.player_id).first()

    winner_p = get_player_by_reg(win_reg_id)
    loser_p = get_player_by_reg(lose_reg_id)

    # THUẬT TOÁN ELO
    K = 32
    Ra = winner_p.elo_points
    Rb = loser_p.elo_points
    E_winner = 1 / (1 + 10 ** ((Rb - Ra) / 400))
    elo_gain = round(K * (1 - E_winner))
    
    winner_p.elo_points += elo_gain
    winner_p.wins += 1
    winner_p.matches_played += 1
    
    loser_p.elo_points -= elo_gain
    loser_p.losses += 1
    loser_p.matches_played += 1

    match.status = "completed"
    match.winner_side = payload.winner_side
    match.winner_registration_id = win_reg_id
    match.result_note = payload.score

    message_suffix = ""
    if match.round_code == "FINAL":
        tournament = db.query(Tournament).filter(Tournament.id == match.tournament_id).first()
        if tournament:
            tournament.status = "finished"
            if hasattr(tournament, 'winner_player_id'):
                tournament.winner_player_id = winner_p.id
            message_suffix = f" Chúc mừng nhà vô địch {winner_p.id}!"
    else:
        if match.next_match_id:
            next_m = db.query(Match).filter(Match.id == match.next_match_id).first()
            if next_m:
                if match.match_no % 2 != 0:
                    next_m.side_a_registration_id = win_reg_id
                else:
                    next_m.side_b_registration_id = win_reg_id

    db.commit()
    return {"message": f"Thành công! {message_suffix}"}

def get_public_bracket_detail(db: Session, tournament_id: int):
    matches = db.query(Match).filter(Match.tournament_id == tournament_id).all()
    
    def get_name(reg_id):
        if not reg_id: return "Chưa xác định"
        reg = db.query(Registration).filter(Registration.id == reg_id).first()
        if not reg: return "Chưa xác định"
        user = db.query(User).join(Player).filter(Player.id == reg.player_id).first()
        return user.full_name if user else "Chưa xác định"

    results = []
    for m in matches:
        results.append({
            "id": m.id, "match_no": m.match_no, "round_code": m.round_code,
            "p1_name": get_name(m.side_a_registration_id),
            "p2_name": get_name(m.side_b_registration_id),
            "winner_side": m.winner_side, "status": m.status,
            "start_time": m.start_time, "score": m.result_note
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
        return u.full_name if u else "VĐV"

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