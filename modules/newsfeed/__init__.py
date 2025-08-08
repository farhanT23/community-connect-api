from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from utils.database import get_db
from modules.newsfeed.schema import NewsFeedResponse
from modules.newsfeed.service import NewsfeedService
from middlewares.auth import optional_get_current_user
from modules.user.models import User

router = APIRouter(prefix="/newsfeed", tags=["newsfeed"])

@router.get("/", response_model=NewsFeedResponse)
async def get_newsfeed(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(optional_get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    service = NewsfeedService(db)
    user_id = current_user["user_id"] if current_user else None
    posts = await service.get_newsfeed(user_id=user_id, page=page, page_size=page_size)
    return {"posts": posts}
