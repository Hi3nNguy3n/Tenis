# backend/app/core/tasks.py
import asyncio
from datetime import datetime
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.models import MailCampaign, Tournament, Registration, Player, User
from app.api.auth import conf
from fastapi_mail import FastMail, MessageSchema, MessageType
from app.crud import crud_tournament

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def start_scheduler():
    """Khởi động con Bot (Gọi trong main.py)"""    
    # 2. Gắn nhiệm vụ gửi email (mỗi 1 phút)
    scheduler.add_job(process_pending_emails, 'interval', minutes=1, id='mail_sender_job', replace_existing=True)
    
    # 3. Gắn nhiệm vụ cập nhật trạng thái giải đấu (mỗi 5 phút)
    scheduler.add_job(update_tournament_statuses_task, 'interval', minutes=5, id='tour_status_job', replace_existing=True)

    scheduler.start()
    logger.info("⚙️ Async Scheduler đã được khởi động! (Chạy song song Dọn rác, Gửi Mail & Cập nhật Giải)")
    
# ==========================================
# JOB 2: HẸN GIỜ GỬI EMAIL TỰ ĐỘNG (MỚI THÊM)
# ==========================================
async def process_pending_emails():
    """Hàm này sẽ chạy ngầm định kỳ để quét và gửi mail."""
    db: Session = SessionLocal()
    try:
        now = datetime.utcnow()
        
        # Tìm các mail đang chờ (pending) VÀ (không hẹn giờ HOẶC đã đến giờ hẹn)
        pending_campaigns = db.query(MailCampaign).filter(
            MailCampaign.status == "pending",
            (MailCampaign.scheduled_at.is_(None)) | (MailCampaign.scheduled_at <= now)
        ).all()

        if not pending_campaigns:
            return

        logger.info(f"📧 [MAIL SCHEDULER] Tìm thấy {len(pending_campaigns)} chiến dịch cần gửi.")
        fm = FastMail(conf)

        for campaign in pending_campaigns:
            try:
                tournament = db.query(Tournament).filter(Tournament.id == campaign.tournament_id).first()
                if not tournament:
                    campaign.status = "failed"
                    continue

                valid_regs = db.query(User.email).join(
                    Player, User.id == Player.user_id
                ).join(
                    Registration, Player.id == Registration.player_id
                ).filter(
                    Registration.tournament_id == tournament.id,
                    Registration.deleted_at.is_(None)
                ).all()
                
                bcc_emails = [reg[0] for reg in valid_regs if reg[0]]

                if not bcc_emails:
                    campaign.status = "failed"
                    continue

                subject = f"🎾 {campaign.subject} - {tournament.name}"
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
                                            <h2 style="color: #146250; margin-top: 0;">{campaign.subject}</h2>
                                            <div style="color: #444; line-height: 1.8; font-size: 16px; white-space: pre-wrap; background-color: #f9fbfb; padding: 20px; border-left: 4px solid #146250; border-radius: 4px;">{campaign.message}</div>
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
                await fm.send_message(message)

                campaign.status = "sent"
                campaign.sent_at = now
                logger.info(f"✅ [MAIL SCHEDULER] Đã gửi thành công chiến dịch ID {campaign.id} cho {len(bcc_emails)} người.")

            except Exception as e:
                logger.error(f"❌ [MAIL SCHEDULER] Lỗi khi gửi chiến dịch ID {campaign.id}: {e}")
                campaign.status = "failed"
        
        db.commit()
    finally:
        db.close()

async def update_tournament_statuses_task():
    """Hàm wrapper cho job scheduler để cập nhật trạng thái giải đấu."""
    db = SessionLocal()
    try:
        updated_count = crud_tournament.auto_update_tournament_statuses(db)
        if updated_count > 0:
            logger.info(f"🏆 [TOUR SCHEDULER] Đã tự động cập nhật trạng thái cho {updated_count} giải đấu.")
    except Exception as e:
        logger.error(f"❌ [TOUR SCHEDULER] Lỗi cập nhật trạng thái: {e}")
    finally:
        db.close()