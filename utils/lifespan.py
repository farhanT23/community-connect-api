
from fastapi import FastAPI
from contextlib import asynccontextmanager

from utils.database import engine, Base
from modules.user.models import User


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield