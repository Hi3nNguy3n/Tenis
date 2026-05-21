from fastapi import APIRouter, Depends, Query, BackgroundTasks, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from datetime import datetime

from app.db.database import get_db
from app.api.deps import get_current_admin, get_current_user
from app.models.models import User, Player, Registration, Tournament, Match, TournamentCategory
from app.crud import crud_tournament
from app.schemas import tournament_schemas, registration_schemas
from app.core.audit import audit_log

import urllib.parse
from app.api.auth import verify_otp
from app.crud import crud_registration
from app.api.registrations import update_qr
router = APIRouter()

# 1. TẠO GIẢI ĐẤU (CHỈ ADMIN)
@router.post("/", response_model=tournament_schemas.TournamentResponse)
@audit_log(module="TOURNAMENT", action="CREATE", event_name="Khởi tạo giải đấu mới")
def create_tournament(
    tournament: tournament_schemas.TournamentCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    return crud_tournament.create_tournament(db=db, tournament=tournament)
    
# 14. XÓA GIẢI ĐẤU (CHỈ ADMIN)
@router.delete("/{tournament_id}")
@audit_log(module="TOURNAMENT", action="DELETE", event_name="Xóa giải đấu")
def delete_tournament(
    tournament_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    return crud_tournament.delete_tournament_db(db, tournament_id)


# 2. XEM DANH SÁCH GIẢI ĐẤU (PUBLIC)
@router.get("/", response_model=List[tournament_schemas.TournamentResponse])
def read_tournaments(
    skip: int = Query(0, description="Bỏ qua bao nhiêu bản ghi đầu"),
    limit: int = Query(10, description="Lấy tối đa bao nhiêu bản ghi"),
    status: str = Query(None, description="Lọc theo trạng thái: draft, open, ongoing, finished"),
    db: Session = Depends(get_db)
):
    return crud_tournament.get_tournaments_with_counts(db, skip=skip, limit=limit, status=status)

# 3. XEM CHI TIẾT 1 GIẢI ĐẤU (PUBLIC)
@router.get("/{tournament_id}", response_model=tournament_schemas.TournamentResponse)
def read_tournament(tournament_id: int, db: Session = Depends(get_db)):
    return crud_tournament.get_tournament_with_count(db, tournament_id=tournament_id)

# 4. THỐNG KÊ TỔNG QUAN (ADMIN ONLY)
@router.get("/summary/stats", dependencies=[Depends(get_current_admin)])
def read_tournament_stats(db: Session = Depends(get_db)):
    return crud_tournament.get_system_stats(db)

# 5. CẬP NHẬT GIẢI ĐẤU (CHỈ ADMIN)
@router.put("/{tournament_id}", response_model=tournament_schemas.TournamentResponse)
@audit_log(module="TOURNAMENT", action="UPDATE", event_name="Cập nhật cấu hình giải đấu")
def update_tournament(
    tournament_id: int,
    tournament_in: tournament_schemas.TournamentCreate, 
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    return crud_tournament.update_tournament_info(db, tournament_id, tournament_in, current_admin.id)

# 5.1 THÊM NỘI DUNG THI ĐẤU VÀO GIẢI (CHỈ ADMIN)
@router.post("/{tournament_id}/categories", response_model=tournament_schemas.TournamentCategoryResponse)
@audit_log(module="TOURNAMENT", action="ADD_CATEGORY", event_name="Thêm nội dung thi đấu")
def add_tournament_category(
    tournament_id: int,
    category: tournament_schemas.TournamentCategoryCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Không tìm thấy giải đấu")
    
    db_category = TournamentCategory(**category.model_dump(), tournament_id=tournament_id)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

# 5.2 XÓA NỘI DUNG THI ĐẤU (CHỈ ADMIN)
@router.delete("/categories/{category_id}")
@audit_log(module="TOURNAMENT", action="DELETE_CATEGORY", event_name="Xóa nội dung thi đấu")
def delete_tournament_category(
    category_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    db_category = db.query(TournamentCategory).filter(TournamentCategory.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Không tìm thấy nội dung thi đấu")
    
    # Kiểm tra xem có ai đăng ký vào nội dung này chưa
    has_regs = db.query(Registration).filter(Registration.tournament_category_id == category_id).first()
    if has_regs:
        raise HTTPException(status_code=400, detail="Không thể xóa nội dung này vì đã có vận động viên đăng ký.")

    db.delete(db_category)
    db.commit()
    return {"message": "Đã xóa nội dung thi đấu thành công"}

# 5.3 CẬP NHẬT NỘI DUNG THI ĐẤU (CHỈ ADMIN)
@router.put("/categories/{category_id}")
@audit_log(module="TOURNAMENT", action="UPDATE_CATEGORY", event_name="Cập nhật nội dung thi đấu")
def update_tournament_category(
    category_id: int,
    category: tournament_schemas.TournamentCategoryCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    db_category = db.query(TournamentCategory).filter(TournamentCategory.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Không tìm thấy nội dung thi đấu")
    
    for key, value in category.model_dump().items():
        setattr(db_category, key, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category

# 6. GENERATE DRAW (ADMIN ONLY)
@router.post("/{tournament_id}/generate-draw", dependencies=[Depends(get_current_admin)])
@audit_log(module="TOURNAMENT", action="GENERATE", event_name="Tạo sơ đồ thi đấu")
def generate_draw(tournament_id: int, request: tournament_schemas.GenerateDrawRequest, db: Session = Depends(get_db)):
    try:
        if request.format_type == "round_robin":
            return crud_tournament.generate_round_robin_draw(db, tournament_id, request.category_id, request.num_groups)
        else:
            return crud_tournament.generate_knockout_draw(db, tournament_id, request.category_id, request.draw_size) 
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# 6.5 KIỂM TRA ĐIỀU KIỆN TRƯỚC KHI ĐĂNG KÝ
@router.post("/{tournament_id}/validate-registration")
def validate_registration_early(
    tournament_id: int,
    payload: tournament_schemas.ValidateRegistrationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Lấy hồ sơ VĐV
    player = db.query(Player).filter(Player.user_id == current_user.id).first()
    if not player:
        raise HTTPException(status_code=400, detail="Vui lòng tạo hồ sơ VĐV trước khi đăng ký.")
        
    player_id = player.id
    # 1. Kiểm tra bản thân
    existing_registrant = db.query(Registration).filter(
        Registration.tournament_id == tournament_id,
        Registration.tournament_category_id == payload.category_id,
        Registration.deleted_at.is_(None),
        or_(
            Registration.player_id == player_id,
            Registration.partner_player_id == player_id
        )
    ).first()
    
    if existing_registrant:
        if existing_registrant.player_id == player_id:
            raise HTTPException(status_code=400, detail="Bạn đã đăng ký nội dung này rồi.")
        else:
            raise HTTPException(status_code=400, detail="Bạn đã được đăng ký làm đồng đội trong một đội khác cho nội dung này.")
            
    # 2. Kiểm tra đồng đội & Giới tính
    category = db.query(TournamentCategory).filter(TournamentCategory.id == payload.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Không tìm thấy nội dung thi đấu.")
    
    # Normalize gender
    def normalize_gender(g):
        if not g: return "unknown"
        g = g.lower()
        if g in ["nam", "male"]: return "male"
        if g in ["nữ", "female"]: return "female"
        return g

    cat_type = category.category_type.lower()
    user_gender = normalize_gender(current_user.gender)

    # Validation cho Đơn
    if cat_type == "mens_singles":
        if user_gender != "male":
            raise HTTPException(status_code=400, detail="Nội dung này chỉ dành cho Nam.")
    elif cat_type == "womens_singles":
        if user_gender != "female":
            raise HTTPException(status_code=400, detail="Nội dung này chỉ dành cho Nữ.")

    if payload.partner_player_id:
        if payload.partner_player_id == player_id:
            raise HTTPException(status_code=400, detail="Bạn không thể chọn chính mình làm đồng đội.")
            
        existing_partner = db.query(Registration).filter(
            Registration.tournament_id == tournament_id,
            Registration.tournament_category_id == payload.category_id,
            Registration.deleted_at.is_(None),
            or_(
                Registration.player_id == payload.partner_player_id,
                Registration.partner_player_id == payload.partner_player_id
            )
        ).first()
        
        if existing_partner:
            raise HTTPException(status_code=400, detail=f"Đồng đội {payload.partner_name or ''} đã đăng ký tham gia nội dung này rồi.")
            
        # Kiểm tra giới tính đồng đội
        partner_user = db.query(User).join(Player).filter(Player.id == payload.partner_player_id).first()
        partner_gender = normalize_gender(partner_user.gender) if partner_user else "unknown"
        
        if cat_type == "mens_doubles":
            if user_gender != "male" or partner_gender != "male":
                raise HTTPException(status_code=400, detail="Nội dung Đôi Nam yêu cầu cả 2 thành viên đều là Nam.")
        elif cat_type == "womens_doubles":
            if user_gender != "female" or partner_gender != "female":
                raise HTTPException(status_code=400, detail="Nội dung Đôi Nữ yêu cầu cả 2 thành viên đều là Nữ.")
        elif cat_type == "mixed_doubles":
            is_valid_mixed = (user_gender == "male" and partner_gender == "female") or \
                             (user_gender == "female" and partner_gender == "male")
            if not is_valid_mixed:
                raise HTTPException(status_code=400, detail="Nội dung Đôi Nam Nữ yêu cầu 1 thành viên Nam và 1 thành viên Nữ.")
    elif "doubles" in cat_type:
        raise HTTPException(status_code=400, detail="Nội dung đánh đôi yêu cầu chọn đồng đội đã liên kết tài khoản.")
            
    return {"status": "ok"}

# 7. XEM DANH SÁCH TRẬN ĐẤU (PUBLIC)
@router.get("/{tournament_id}/matches")
def read_tournament_matches(
    tournament_id: int, 
    category_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    return crud_tournament.get_tournament_matches_detail(db, tournament_id=tournament_id, category_id=category_id)

# 8. GÁN LỊCH THI ĐẤU (ADMIN ONLY)
@router.post("/matches/{match_id}/schedule", dependencies=[Depends(get_current_admin)])
@audit_log(module="MATCH", action="UPDATE", event_name="Gán lịch và phân sân thi đấu")
def schedule_match(match_id: int, payload: tournament_schemas.MatchScheduleUpdate, db: Session = Depends(get_db)):
    return crud_tournament.schedule_match_db(db, match_id, payload)

# 8.5 GHÉP CẶP THI ĐẤU THỦ CÔNG (ADMIN ONLY)
@router.put("/matches/{match_id}/assign-players", dependencies=[Depends(get_current_admin)])
@audit_log(module="MATCH", action="ASSIGN_PLAYERS", event_name="Ghép cặp thi đấu thủ công")
def assign_match_players(match_id: int, payload: tournament_schemas.AssignMatchPlayersRequest, db: Session = Depends(get_db)):
    from app.models.models import Match
    from fastapi import HTTPException
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Không tìm thấy trận đấu")
        
    # 1. Validation: Không thể tự đối đầu với chính mình
    if payload.side_a_registration_id and payload.side_a_registration_id == payload.side_b_registration_id:
        raise HTTPException(status_code=400, detail="Không thể xếp một VĐV/cặp đấu tự đối đầu với chính mình.")
    match.side_a_registration_id = payload.side_a_registration_id
    match.side_b_registration_id = payload.side_b_registration_id
    
    db.commit()
    return {"message": "Đã ghép cặp thi đấu thành công"}

# 9. LẤY TẤT CẢ TRẬN ĐẤU (PUBLIC - hiển thị trên trang Lịch thi đấu)
@router.get("/matches/all")
def read_all_matches(db: Session = Depends(get_db)):
    return crud_tournament.get_all_matches_detail(db)

# 10. CẬP NHẬT TỶ SỐ, THĂNG HẠNG & TÍNH ĐIỂM ELO
@router.post("/matches/{match_id}/score", dependencies=[Depends(get_current_admin)])
@audit_log(module="MATCH", action="UPDATE", event_name="Cập nhật tỷ số trận đấu")
def update_match_score(match_id: int, payload: tournament_schemas.MatchScoreUpdate, db: Session = Depends(get_db)):
    return crud_tournament.calculate_elo_and_update_match(db, match_id, payload)

# 11. XEM BRACKET CÔNG KHAI
@router.get("/{tournament_id}/public-bracket")
def get_public_bracket(
    tournament_id: int, 
    category_id: Optional[int] = Query(None, description="Lọc theo nội dung thi đấu"),
    db: Session = Depends(get_db)
):
    return crud_tournament.get_public_bracket_detail(db, tournament_id=tournament_id, category_id=category_id)

# # 12. XUẤT BÁO CÁO EXCEL (ADMIN ONLY)
@router.get("/{tournament_id}/export-excel", dependencies=[Depends(get_current_admin)])
@audit_log(module="TOURNAMENT", action="EXPORT", event_name="Xuất file Excel báo cáo giải đấu")
def export_tournament_excel(tournament_id: int, db: Session = Depends(get_db)):
    # Lấy stream dữ liệu và tên file từ CRUD
    file_stream, file_name = crud_tournament.export_tournament_data_to_excel(db, tournament_id)
    
    # --- PHẦN SỬA LỖI TIẾNG VIỆT ---
    # Mã hóa tên file để tránh lỗi UnicodeEncodeError (latin-1)
    # Ví dụ: "Giải_đấu.xlsx" -> "Gi%E1%BA%A3i_%C4%91%E1%BA%A5u.xlsx"
    encoded_file_name = urllib.parse.quote(file_name)
    
    headers = {
        # Sử dụng filename* để báo cho trình duyệt biết đây là tên file có mã hóa UTF-8
        'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_file_name}",
        'Access-Control-Expose-Headers': 'Content-Disposition'
    }
    # -------------------------------
    
    # Lấy toàn bộ dữ liệu nhị phân một lần
    excel_data = file_stream.getvalue()
    
    return Response(
        content=excel_data, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )

# 13. GỬI EMAIL THÔNG BÁO HÀNG LOẠT (ADMIN ONLY)
@router.post("/{tournament_id}/send-notifications", dependencies=[Depends(get_current_admin)])
async def send_tournament_notifications(
    tournament_id: int, 
    request: tournament_schemas.AnnouncementRequest, # Đảm bảo file schemas đã có scheduled_at
    db: Session = Depends(get_db)
):
    tournament, bcc_emails = crud_tournament.get_tournament_and_valid_emails(db, tournament_id)

    if not tournament:
        raise HTTPException(status_code=404, detail="Không tìm thấy giải đấu")
    if not bcc_emails:
        raise HTTPException(status_code=400, detail="Không có VĐV nào hợp lệ.")

    # 1. Xác định thời gian gửi
    schedule_time = request.scheduled_at
    status = "pending" # Trạng thái chờ Scheduler quét

    # 2. LƯU YÊU CẦU VÀO DATABASE
    crud_tournament.save_mail_campaign(
        db=db, 
        tournament_id=tournament_id, 
        subject=request.subject, 
        message=request.message, 
        total_recipients=len(bcc_emails),
        scheduled_at=schedule_time,
        status=status
    )

    # 3. Trả về thông báo cho Frontend
    if schedule_time:
        return {"message": f"Đã lên lịch gửi thông báo vào lúc {schedule_time.strftime('%d/%m/%Y %H:%M')}."}
    else:
        return {"message": "Đã lưu yêu cầu. Hệ thống sẽ tự động gửi trong ít phút tới."}
    
@router.get("/{tournament_id}/standings")
def get_tournament_standings(
    tournament_id: int, 
    category_id: Optional[int] = Query(None, description="Lọc theo nội dung thi đấu"),
    db: Session = Depends(get_db)
):
    """API tính điểm và xếp hạng Vòng tròn"""
    # Gọi trực tiếp hàm tính điểm từ crud_tournament
    return crud_tournament.calculate_tournament_standings(db, tournament_id, category_id)

@router.post("/{tournament_id}/generate-playoffs", dependencies=[Depends(get_current_admin)])
@audit_log(module="TOURNAMENT", action="GENERATE_PLAYOFF", event_name="Tạo vòng Playoff từ Vòng bảng")
def generate_tournament_playoffs(
    tournament_id: int, 
    request: tournament_schemas.PlayoffRequest,
    db: Session = Depends(get_db)
):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Không tìm thấy giải đấu")

    try:
        return crud_tournament.generate_playoff_draw(db, tournament_id, request.category_id, request.advancers_per_group)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/{tournament_id}/register")
def register_tournament_with_otp(
    tournament_id: int, 
    request: tournament_schemas.TournamentRegisterRequest, 
    background_tasks: BackgroundTasks, # 1. Thêm cái này vào param
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Xác thực OTP
    if not verify_otp(current_user.email, request.otp):
        raise HTTPException(status_code=400, detail="Mã OTP không chính xác hoặc đã hết hạn.")

    try:
        player = db.query(Player).filter(Player.user_id == current_user.id).first()
        if not player:
            raise HTTPException(status_code=404, detail="Hồ sơ vận động viên không tồn tại.")

        # 2. Lưu database (bây giờ nó sẽ auto return status = confirmed)
        reg = crud_registration.register_with_otp_flow(
            db=db,
            tournament_id=tournament_id,
            category_id=request.category_id,
            player_id=player.id,
            notes=request.notes,
            partners=request.partners
        )
        
        # 3. Lấy tên giải đấu và Kích hoạt tạo mã QR ngầm
        tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
        tourn_name = tournament.name if tournament else "Saigon Tennis"
        background_tasks.add_task(update_qr, reg.id, tourn_name)

        return reg

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{tournament_id}/registrations")
def get_public_registrations(
    tournament_id: int, 
    category_id: Optional[int] = Query(None, description="Lọc theo nội dung thi đấu"),
    db: Session = Depends(get_db)
):
    """API công khai: Lấy danh sách VĐV đã xác nhận tham gia"""
    query = db.query(Registration, Player, User, TournamentCategory).join(
        Player, Registration.player_id == Player.id
    ).join(
        User, Player.user_id == User.id
    ).outerjoin(
        TournamentCategory, Registration.tournament_category_id == TournamentCategory.id
    ).filter(
        Registration.tournament_id == tournament_id,
        Registration.status.in_(["pending", "approved", "confirmed", "paid", "checked_in"]),
        Registration.deleted_at.is_(None)
    )
    
    if category_id:
        query = query.filter(Registration.tournament_category_id == category_id)
        
    results = query.order_by(Registration.registered_at.asc()).all()

    response_items = []
    for reg, player, user, category in results:
        item = registration_schemas.RegistrationResponse.model_validate(reg)
        item.player_name = user.full_name
        item.user_id = user.id
        item.player_phone = user.phone 
        item.player_skill = player.skill_level
        item.category_id = reg.tournament_category_id
        item.category_name = category.name if category else "Mặc định"
        
        # Lấy thông tin partner chi tiết (nếu có)
        if reg.partner_user_id:
            p_user = db.query(User).filter(User.id == reg.partner_user_id).first()
            if p_user:
                item.partner_name = p_user.full_name
                item.partner_user_id = p_user.id
                item.partner_avatar = p_user.avatar_url
        elif reg.partner_player_id:
            p_user = db.query(User).join(Player).filter(Player.id == reg.partner_player_id).first()
            if p_user:
                item.partner_name = p_user.full_name
                item.partner_user_id = p_user.id
                item.partner_avatar = p_user.avatar_url

        response_items.append(item)
        
    return response_items
