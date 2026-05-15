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
    scheduler.add_job(process_pending_emails, 'interval', minutes=1, id='mail_sender_job', replace_existing=True)
    scheduler.add_job(update_tournament_statuses_task, 'interval', minutes=5, id='tour_status_job', replace_existing=True)
    scheduler.start()
    logger.info('Async Scheduler started.')
    
async def process_pending_emails():
    db = None
    try:
        db = SessionLocal()
        now = datetime.utcnow()
        try:
            pending_campaigns = db.query(MailCampaign).filter(
                MailCampaign.status == 'pending',
                (MailCampaign.scheduled_at.is_(None)) | (MailCampaign.scheduled_at <= now)
            ).all()
        except Exception as conn_err:
            logger.error(f'Database connection error in mail scheduler: {conn_err}')
            return
        if not pending_campaigns:
            return
        fm = FastMail(conf)
        for campaign in pending_campaigns:
            try:
                tournament = db.query(Tournament).filter(Tournament.id == campaign.tournament_id).first()
                if not tournament:
                    campaign.status = 'failed'
                    continue
                valid_regs = db.query(User.email).join(Player, User.id == Player.user_id).join(Registration, Player.id == Registration.player_id).filter(Registration.tournament_id == tournament.id, Registration.deleted_at.is_(None)).all()
                bcc_emails = [reg[0] for reg in valid_regs if reg[0]]
                if not bcc_emails:
                    campaign.status = 'failed'
                    continue
                subject = f'{campaign.subject} - {tournament.name}'
                message = MessageSchema(subject=subject, recipients=[], bcc=bcc_emails, body=f'{campaign.message}', subtype=MessageType.html)
                await fm.send_message(message)
                campaign.status = 'sent'
                campaign.sent_at = now
            except Exception as e:
                logger.error(f'Mail Scheduler error: {e}')
                campaign.status = 'failed'
        db.commit()
    except Exception as e:
        logger.error(f'Mail Scheduler critical: {e}')
        if db: db.rollback()
    finally:
        if db: db.close()

async def update_tournament_statuses_task():
    db = None
    try:
        db = SessionLocal()
        updated_count = crud_tournament.auto_update_tournament_statuses(db)
        if updated_count > 0:
            logger.info(f'Tour Scheduler: Updated {updated_count} statuses.')
    except Exception as e:
        logger.error(f'Tour Scheduler error: {e}')
    finally:
        if db: db.close()

