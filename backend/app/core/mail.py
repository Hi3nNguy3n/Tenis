from fastapi import HTTPException
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.core.config import settings


conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)


async def send_email(email_to: str, subject: str, html_content: str):
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=html_content,
        subtype=MessageType.html
    )
    try:
        await FastMail(conf).send_message(message)
    except Exception as e:
        print(f"[SMTP EMAIL ERROR]: {e}")
        raise HTTPException(
            status_code=500,
            detail="Không thể gửi email lúc này. Vui lòng thử lại sau."
        )


async def send_bulk_email(bcc_emails: list[str], subject: str, html_content: str):
    message = MessageSchema(
        subject=subject,
        recipients=[],
        bcc=bcc_emails,
        body=html_content,
        subtype=MessageType.html
    )
    await FastMail(conf).send_message(message)
