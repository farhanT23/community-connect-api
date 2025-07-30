from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Request, status, Form, UploadFile, File
from httpx import Response
from sqlalchemy.ext.asyncio import AsyncSession

from utils.database import get_db
from middlewares.auth import get_current_user, optional_get_current_user
from utils.error_response import ErrorResponse
from .models import PrivacyEnum

from .schema import PostOut, ReactionTypeEnum
from .services import PostService
from ..user.schema import ReactionResponse

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

@router.post("/create", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_post(
    request: Request,
    content: Optional[str] = Form(None),
    privacy: PrivacyEnum = Form(...),
    media_files: Optional[List[UploadFile]] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    service = PostService(db)

    post = await service.create_post(
        user_id=current_user["user_id"],
        content=content,
        privacy=privacy,
        media_files=media_files or []
    )

    return post

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    service = PostService(db)
    await service.delete_post(post_id, current_user["user_id"])
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/{post_id}/edit", response_model=PostOut)
async def edit_post(
    post_id: int,
    content: Optional[str] = Form(None),
    privacy: PrivacyEnum = Form(PrivacyEnum.PUBLIC),
    media_files: Optional[List[UploadFile]] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    service = PostService(db)
    return await service.edit_post(
        post_id=post_id,
        user_id=current_user["user_id"],
        content=content,
        privacy=privacy,
        media_files=media_files
    )

@router.delete("/{post_id}/media/{media_id}/remove")
async def remove_post_media(
    post_id: int,
    media_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    service = PostService(db)
    await service.remove_post_media(
        post_id=post_id,
        media_id=media_id,
        user_id=current_user["user_id"]
    )
    return {"detail": "Media removed successfully"}

@router.post("/{post_id}/reaction/{reaction_type}", response_model=ReactionResponse)
async def post_reaction(
        post_id:int,
        reaction_type: ReactionTypeEnum,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    service = PostService(db)
    response = await service.react_to_post(
        post_id=post_id,
        user_id=current_user["user_id"],
        reaction_type=reaction_type
    )
    return response

