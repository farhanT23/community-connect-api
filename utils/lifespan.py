
from fastapi import FastAPI
from contextlib import asynccontextmanager

from utils.database import engine, Base
from modules.user.models import User
from modules.post.models import Post, Media, Reaction, Comment


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield