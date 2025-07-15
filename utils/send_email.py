
from typing import Any, Dict
import os
from fastapi_mail import ConnectionConfig, MessageType
from config import mail_settings as settings
from config import app_settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.smtp_user,
    MAIL_PASSWORD=settings.smtp_password,
    MAIL_FROM=settings.email_from,
    MAIL_PORT=settings.smtp_port,
    MAIL_SERVER=settings.smtp_host,
    MAIL_FROM_NAME=app_settings.app_name,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=os.path.join(os.path.dirname(__file__), "templates"),
)

async def send_mail(subject: str, recipients: list[str],data:Dict[str,Any]={},template: str|None=None) -> None:
    from fastapi_mail import FastMail, MessageSchema
    
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        template_body=data,
        subtype=MessageType.html
    )
    fm = FastMail(conf)

    await fm.send_message(message,
        template_name=template)