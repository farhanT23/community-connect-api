from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from utils.database import get_db
from middlewares.auth import get_current_user, optional_get_current_user
from utils.error_response import ErrorResponse

from .schema import PostOut
from .services import PostService

router = APIRouter(
    prefix="/posts",
    tags=["posts"],
    responses={
        404: {"model": ErrorResponse},
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
    },
)


@router.get("/health")
async def health():
    return {"message": "Post module is up"}


@router.get("/{post_id}", response_model=PostOut)
async def get_post_detail(
    request: Request,
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(optional_get_current_user)
):
    user_id = current_user["user_id"] if current_user else None
    post = await PostService(db).get_post_detail(post_id, user_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return post

