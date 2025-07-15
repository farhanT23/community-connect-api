# modules/post/service.py

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from modules.post.models import Post, Reaction, Comment
from modules.post.schema import PostOut, PostShareOut, UserSummaryOut, MediaOut


class PostService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_post_detail(self, post_id: int, current_user_id: int | None) -> PostOut:
        query = (
            select(Post)
            .options(
                selectinload(Post.user),
                selectinload(Post.tagged_media),
                selectinload(Post.original_post).selectinload(Post.user),
                selectinload(Post.original_post).selectinload(Post.tagged_media)
            )
            .where(Post.id == post_id)
        )
        result = await self.db.execute(query)
        post = result.scalar_one_or_none()

        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        if post.privacy.name == "only_me":
            if not current_user_id or current_user_id != post.user_id:
                raise HTTPException(status_code=403, detail="This post is private")

        reaction_count = await self._count(Reaction, Reaction.post_id == post.id)
        comment_count = await self._count(Comment, Comment.post_id == post.id)
        share_count = await self._count(Post, Post.original_post_id == post.id)

        user_out = UserSummaryOut(
            id=post.user.id,
            name=post.user.name,
            profile_image=post.user.profile_image,
        )

        media_out = [
            MediaOut(id=m.id, file=m.file)
            for m in post.tagged_media
        ]

        original_post_out = None
        if post.original_post:
            original_user = UserSummaryOut(
                id=post.original_post.user.id,
                name=post.original_post.user.name,
                profile_image=post.original_post.user.profile_image,
            )
            original_media = [
                MediaOut(id=m.id, file=m.file)
                for m in post.original_post.tagged_media
            ]
            original_post_out = PostShareOut(
                id=post.original_post.id,
                content=post.original_post.content,
                privacy=post.original_post.privacy,
                user=original_user,
                tagged_media=original_media,
                created_at=post.original_post.created_at,
                updated_at=post.original_post.updated_at,
            )

        return PostOut(
            id=post.id,
            user=user_out,
            content=post.content,
            privacy=post.privacy,
            tagged_media=media_out,
            reaction_count=reaction_count,
            comment_count=comment_count,
            share_count=share_count,
            created_at=post.created_at,
            updated_at=post.updated_at,
            original_post=original_post_out
        )

    async def _count(self, model, *filters):
        query = select(func.count()).select_from(model).filter(*filters)
        result = await self.db.execute(query)
        return result.scalar_one()
