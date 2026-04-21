# backend/app/api/tournaments.py
from fastapi import APIRouter, Depends, Query, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from pydantic import BaseModel

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.models.models import User, Player, Registration, Tournament, Match
from app.crud import crud_tournament
from app.schemas import tournament_schemas
from app.core.audit import audit_log
from fastapi.responses import Response

from fastapi_mail import FastMail, MessageSchema, MessageType
from app.api.auth import conf
import urllib.parse
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

# 6. GENERATE DRAW (ADMIN ONLY)
class GenerateDrawRequest(BaseModel):
    format_type: str = "knockout" # Hoặc "round_robin"
    num_groups: int = 1           # Số bảng đấu

@router.post("/{tournament_id}/generate-draw", dependencies=[Depends(get_current_admin)])
@audit_log(module="TOURNAMENT", action="GENERATE_DRAW", event_name="Tạo lịch thi đấu")
def generate_tournament_draw(
    tournament_id: int, 
    request: GenerateDrawRequest, # Nhận payload từ Frontend
    db: Session = Depends(get_db)
):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Không tìm thấy giải đấu")

    try:
        # Gọi "Thủ kho" ra làm việc tùy theo thể thức
        if request.format_type == "round_robin":
            return crud_tournament.generate_round_robin_draw(db, tournament_id, request.num_groups)
        else:
            # Code cũ của ông cho đấu loại trực tiếp
            return crud_tournament.generate_draw(db, tournament_id) 
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# 7. XEM DANH SÁCH TRẬN ĐẤU (PUBLIC)
@router.get("/{tournament_id}/matches")
def read_tournament_matches(tournament_id: int, db: Session = Depends(get_db)):
    return crud_tournament.get_tournament_matches_detail(db, tournament_id=tournament_id)

class MatchScheduleUpdate(BaseModel):
    court_id: int
    start_time: datetime

# 8. GÁN LỊCH THI ĐẤU (ADMIN ONLY)
@router.post("/matches/{match_id}/schedule", dependencies=[Depends(get_current_admin)])
@audit_log(module="MATCH", action="UPDATE", event_name="Gán lịch và phân sân thi đấu")
def schedule_match(match_id: int, payload: MatchScheduleUpdate, db: Session = Depends(get_db)):
    return crud_tournament.schedule_match_db(db, match_id, payload)

# 9. LẤY TẤT CẢ TRẬN ĐẤU (PUBLIC - hiển thị trên trang Lịch thi đấu)
@router.get("/matches/all")
def read_all_matches(db: Session = Depends(get_db)):
    return crud_tournament.get_all_matches_detail(db)

class MatchScoreUpdate(BaseModel):
    score: str        
    winner_side: str  

# 10. CẬP NHẬT TỶ SỐ, THĂNG HẠNG & TÍNH ĐIỂM ELO
@router.post("/matches/{match_id}/score", dependencies=[Depends(get_current_admin)])
@audit_log(module="MATCH", action="UPDATE", event_name="Cập nhật tỷ số trận đấu")
def update_match_score(match_id: int, payload: MatchScoreUpdate, db: Session = Depends(get_db)):
    return crud_tournament.calculate_elo_and_update_match(db, match_id, payload)

# 11. XEM BRACKET CÔNG KHAI
@router.get("/{tournament_id}/public-bracket")
def get_public_bracket(tournament_id: int, db: Session = Depends(get_db)):
    return crud_tournament.get_public_bracket_detail(db, tournament_id=tournament_id)

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
class AnnouncementRequest(BaseModel):
    subject: str
    message: str

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
def get_tournament_standings(tournament_id: int, db: Session = Depends(get_db)):
    """API tính điểm và xếp hạng Vòng tròn"""
    # Gọi trực tiếp hàm tính điểm từ crud_tournament
    return crud_tournament.calculate_tournament_standings(db, tournament_id)

class PlayoffRequest(BaseModel):
    advancers_per_group: int = 2 # Mặc định lấy Top 2 mỗi bảng

@router.post("/{tournament_id}/generate-playoffs", dependencies=[Depends(get_current_admin)])
@audit_log(module="TOURNAMENT", action="GENERATE_PLAYOFF", event_name="Tạo vòng Playoff từ Vòng bảng")
def generate_tournament_playoffs(
    tournament_id: int, 
    request: PlayoffRequest,
    db: Session = Depends(get_db)
):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Không tìm thấy giải đấu")

    try:
        return crud_tournament.generate_playoff_draw(db, tournament_id, request.advancers_per_group)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))