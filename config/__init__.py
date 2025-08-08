from pathlib import Path
from dotenv import load_dotenv
load_dotenv(override=True)

from .mail import MailSettings
from dotenv import load_dotenv
load_dotenv(override=True)


from .mail import MailSettings

from .app import AppSettings
from .database import DatabaseSettings
from .jwt import JWTSettings

mail_settings = MailSettings()
app_settings = AppSettings()
db_settings = DatabaseSettings()
jwt_settings = JWTSettings()

BASE_PATH = Path(__file__).resolve().parent.parent

