# backend/app/api/tournaments.py
from fastapi import APIRouter, Depends, Query, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from pydantic import BaseModel

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.models.models import User, Player, Registration
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
@router.post("/{tournament_id}/generate-draw", dependencies=[Depends(get_current_admin)])
@audit_log(module="TOURNAMENT", action="UPDATE", event_name="Tự động sinh sơ đồ nhánh đấu (Bracket)")
def generate_tournament_draw(tournament_id: int, db: Session = Depends(get_db)):
    return crud_tournament.generate_knockout_draw(db, tournament_id=tournament_id)

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

# 9. LẤY TẤT CẢ TRẬN ĐẤU (ADMIN ONLY)
@router.get("/matches/all", dependencies=[Depends(get_current_admin)])
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
    request: AnnouncementRequest, # <-- Nhận dữ liệu từ body
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    tournament, bcc_emails = crud_tournament.get_tournament_and_valid_emails(db, tournament_id)

    if not tournament:
        raise HTTPException(status_code=404, detail="Không tìm thấy giải đấu")
    if not bcc_emails:
        raise HTTPException(status_code=400, detail="Không có VĐV nào hợp lệ.")

    # Sử dụng Subject và Message từ Admin nhập vào
    subject = f"🎾 {request.subject} - {tournament.name}"
    # Thiết kế lại nội dung Email chuyên nghiệp
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6;">
        <table border="0" cellpadding="0" cellspacing="0" width="100%">
            <tr>
                <td align="center" style="padding: 20px 0;">
                    <table border="0" cellpadding="0" cellspacing="0" width="600" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
                        <tr>
                            <td align="center" style="background-color: #146250; padding: 40px 20px;">
                                <h1 style="color: #ffffff; margin: 0; font-size: 24px; text-transform: uppercase; letter-spacing: 2px;">Saigon Tennis Tours</h1>
                                <p style="color: #d1e7dd; margin: 10px 0 0 0; font-size: 14px;">Hệ thống quản lý giải đấu chuyên nghiệp</p>
                            </td>
                        </tr>
                        
                        <tr>
                            <td style="padding: 40px 30px;">
                                <h2 style="color: #146250; margin-top: 0;">{request.subject}</h2>
                                <div style="color: #444; line-height: 1.8; font-size: 16px; white-space: pre-wrap; background-color: #f9fbfb; padding: 20px; border-left: 4px solid #146250; border-radius: 4px;">
{request.message}
                                </div>
                                
                                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
                                    <tr>
                                        <td>
                                            <p style="margin: 5px 0; color: #666; font-size: 14px;"><strong>Giải đấu:</strong> {tournament.name}</p>
                                            <p style="margin: 5px 0; color: #666; font-size: 14px;"><strong>Địa điểm:</strong> {tournament.location}</p>
                                            <p style="margin: 5px 0; color: #666; font-size: 14px;"><strong>Thời gian:</strong> {tournament.start_date}</p>
                                        </td>
                                    </tr>
                                </table>

                                <div style="margin-top: 30px; text-align: center;">
                                    <a href="http://localhost:5173" style="background-color: #146250; color: #ffffff; padding: 15px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">Xem Chi Tiết Giải Đấu</a>
                                </div>
                            </td>
                        </tr>

                        <tr>
                            <td style="background-color: #f9f9f9; padding: 20px; text-align: center; color: #999; font-size: 12px;">
                                <p style="margin: 0;">Đây là thông báo tự động từ hệ thống quản lý giải đấu Saigon Tennis Tours.</p>
                                <p style="margin: 5px 0 0 0;">© 2026 Saigon Tennis. All rights reserved.</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    message = MessageSchema(
        subject=subject,
        recipients=[], 
        bcc=bcc_emails, 
        body=html_body,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)

    return {"message": f"Hệ thống đang gửi thông báo tùy chỉnh đến {len(bcc_emails)} VĐV."}