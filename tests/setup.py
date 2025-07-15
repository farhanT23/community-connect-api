from fastapi.testclient import TestClient
from fastapi import FastAPI, status
from httpx import AsyncClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from config.database import DatabaseSettings
from main import app
from utils.database import Base, get_db

engine = create_async_engine(
    "sqlite+aiosqlite:///./test.db",
    echo=True,
    )
async_session = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
async def get_test_db():
    async with async_session() as session:
        yield session


app.dependency_overrides[get_db] = get_test_db


client = TestClient(app)