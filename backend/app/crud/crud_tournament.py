# backend/app/crud/crud_tournament.py
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from fastapi import HTTPException
from datetime import datetime
import math
import random

from app.models.models import Tournament, Match, Registration, Player, User, Payment, Court, MailCampaign
from app.schemas.tournament_schemas import TournamentCreate, TournamentUpdate
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
        raise HTTPException(status_code=400, detail="Chưa có vận động viên nào được duyệt tham gia để tạo nhánh đấu.")
    
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
            "court_id": m.court_id, 
            "start_time": m.start_time.isoformat() if m.start_time else None, 
            "winner_side": m.winner_side
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

    # Helper lấy tên VĐV từ registration_id
    def get_player_name(reg_id):
        if not reg_id:
            return None
        reg = db.query(Registration).filter(Registration.id == reg_id).first()
        if not reg:
            return None
        user = db.query(User).join(Player, Player.user_id == User.id).filter(Player.id == reg.player_id).first()
        return user.full_name if user else None

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

def generate_round_robin_draw(db: Session, tournament_id: int, num_groups: int = 1):
    """Thuật toán chia bảng và tạo lịch thi đấu Vòng tròn"""
    
    # 1. Lấy danh sách VĐV đã xác nhận tham gia
    players = db.query(Registration).filter(
        Registration.tournament_id == tournament_id,
        Registration.status == "confirmed",
        Registration.deleted_at.is_(None)
    ).all()

    if len(players) < 2:
        raise HTTPException(status_code=400, detail="Cần ít nhất 2 VĐV đã duyệt để tạo lịch thi đấu vòng tròn.")

    # 2. Xóa lịch thi đấu cũ (nếu có) để tạo lại
    db.query(Match).filter(Match.tournament_id == tournament_id).delete()
    
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

def calculate_tournament_standings(db: Session, tournament_id: int):
    """Hàm lõi tính điểm vòng tròn (Dùng chung cho cả API và Playoff)"""
    matches = db.query(Match).filter(
        Match.tournament_id == tournament_id,
        Match.stage_type == "group_stage",
        Match.status == "completed" 
    ).all()

    standings = {}

    def safe_int(val):
        return int(val) if val is not None else 0

    for match in matches:
        group = f"Bảng {match.group_id}"
        if group not in standings:
            standings[group] = {}

        p1_id = match.side_a_registration_id
        p2_id = match.side_b_registration_id

        if not p1_id or not p2_id:
            continue

        for p_id in [p1_id, p2_id]:
            if p_id not in standings[group]:
                user_record = db.query(User.full_name).join(
                    Player, User.id == Player.user_id
                ).join(
                    Registration, Player.id == Registration.player_id
                ).filter(
                    Registration.id == p_id
                ).first()
                
                player_name = user_record[0] if user_record else "Unknown"
                    
                standings[group][p_id] = {
                    "player_name": player_name, 
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

def generate_playoff_draw(db: Session, tournament_id: int, advancers_per_group: int = 2):
    """Thuật toán tự động chốt vòng bảng và xếp cặp Playoff"""
    
    # 1. Gọi hàm cục bộ tính Bảng xếp hạng để lấy Top VĐV
    standings_data = calculate_tournament_standings(db=db, tournament_id=tournament_id)
    
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

    # 4. Ghi các trận Playoff vào Database
    db.query(Match).filter(
        Match.tournament_id == tournament_id,
        Match.stage_type == "playoff"
    ).delete()

    for idx, pair in enumerate(match_pairs):
        new_match = Match(
            tournament_id=tournament_id,
            stage_type="playoff",
            round_code="SF" if len(match_pairs) > 1 else "F",
            match_no=idx + 1,
            side_a_registration_id=pair[0]["registration_id"],
            side_b_registration_id=pair[1]["registration_id"],
            status="scheduled",
            best_of_sets=3
        )
        db.add(new_match)

    db.commit()
    return {"message": f"Đã chốt sổ Vòng bảng và tạo {len(match_pairs)} trận Playoff thành công!"}