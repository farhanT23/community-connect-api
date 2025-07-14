from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from config import app_settings, db_settings


if db_settings.database_driver == "sqlite":
    DATABASE_URL = f"{db_settings.database_driver}+aiosqlite:///{db_settings.database_name}.db"
else:
    DATABASE_URL = f"{db_settings.database_driver}://{db_settings.database_user}:{db_settings.database_password}@{db_settings.database_host}:{db_settings.database_port}/{db_settings.database_name}"

# Async engine for PostgreSQL (or any supported DB)
engine = create_async_engine(
    DATABASE_URL,
    echo=app_settings.env == "dev",
)

# Async session factory
async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Dependency to use in FastAPI routes
async def get_db():
    async with async_session() as session:
        yield session




Base = declarative_base()
