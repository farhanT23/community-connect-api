# app/database/session.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from app.config import get_settings

settings = get_settings()

# SQLAlchemy connection string
DATABASE_URL = (
    f"mysql+mysqlconnector://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}"
    f"@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,       # Ensures stale connections are refreshed
    echo=False                # Set to True to log SQL queries (for debugging)
)

# Session factory
SessionLocal = scoped_session(sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
))

# Declarative base for models to inherit
Base = declarative_base()
