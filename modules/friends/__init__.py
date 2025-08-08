
from typing import List
from fastapi import APIRouter, Depends, Request, Response, UploadFile,status
from sqlalchemy.ext.asyncio import AsyncSession


from middlewares.auth import get_current_user, optional_get_current_user
from utils.error_response import ErrorResponse
from utils.database import get_db

from ..user.schema import (
    UserSchema
    )
from .service import FriendService

router = APIRouter(
    prefix="/friends",
    tags=["friend"],
    responses={
        404: {"model": ErrorResponse},
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        200: {"model": ErrorResponse},
        },
)



@router.get("/health")
async def health():
    return {"message": "Up"}


@router.get('/find-friends',response_model=List[UserSchema],)
async def get_user(
    request:Request,
    db:AsyncSession=Depends(get_db),
    current_user:dict|None=Depends(optional_get_current_user)
    ):
    friends_service = FriendService(db)

    current_user_id = current_user["user_id"] if current_user else None

    user = await friends_service.get_all_users(current_user_id)

    return user

@router.post('/toggle_follow/{follower_id}')
async def toggle_follow(
    request:Request,
    follower_id:int,
    db:AsyncSession=Depends(get_db),
    current_user:dict=Depends(get_current_user)
    ):
    friends_service = FriendService(db)
    await friends_service.toggle_follow(current_user['user_id'],follower_id)

    return {"detail":"Success"}