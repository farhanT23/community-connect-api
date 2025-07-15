from dotenv import load_dotenv
load_dotenv(override=True)

from .app import AppSettings
from .database import DatabaseSettings
from .jwt import JWTSettings

app_settings = AppSettings()
db_settings = DatabaseSettings()
jwt_settings = JWTSettings()