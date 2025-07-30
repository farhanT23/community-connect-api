

from config.base import BaseBaseSettings


class MailSettings(BaseBaseSettings):
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    email_from: str

    