from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, aliased
from modules.post.models import Post, Reaction, Comment, Media
from modules.user.models import User

class PostRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    async def get_post_with_details(self, post_id: int, current_user_id):
        P2 = aliased(Post)
        reaction_count_sub = select(func.count(Reaction.id)).where(Reaction.post_id == Post.id).scalar_subquery()
        comment_count_sub = select(func.count(Comment.id)).where(Comment.post_id == Post.id).scalar_subquery()
        share_count_sub = select(func.count(P2.id)).where(P2.original_post_id == Post.id).scalar_subquery()

        query = (
            select(
                Post,
                reaction_count_sub.label("reaction_count"),
                comment_count_sub.label("comment_count"),
                share_count_sub.label("share_count"),
            )
            .options(
                selectinload(Post.user),
                selectinload(Post.tagged_media),
                selectinload(Post.original_post).selectinload(Post.user),
                selectinload(Post.original_post).selectinload(Post.tagged_media),
            )
            .where(Post.id == post_id)
        )

        if current_user_id:
            user_reaction_sub = (
                select(Reaction.type)
                .where((Reaction.post_id == Post.id) & (Reaction.user_id == current_user_id))
                .scalar_subquery()
            )
            query = query.add_columns(user_reaction_sub.label("reaction_type"))

        result = await self.db.execute(query)

        return result.one_or_none()
    
    async def get_user_posts(self, user_id: int, limit: int, offset: int):
        query = (
            select(Post)
            .where(Post.user_id == user_id)
            .options(
                selectinload(Post.user),
                selectinload(Post.tagged_media),
                selectinload(Post.original_post).selectinload(Post.user),
                selectinload(Post.original_post).selectinload(Post.tagged_media),
            ).order_by(Post.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_post_with_media(self, post_id: int):
        query = select(Post).where(Post.id == post_id).options(selectinload(Post.tagged_media))
        result = await self.db.execute(query)
        return result.one_or_none()
    
    async def get_user_by_id(self, user_id: int):
        return await self.db.get(User, user_id)
    
    async def add_and_refresh(self, post: Post):
        self.db.add(post)
        await self.db.flush()
        await self.db.refresh(post)
        return post
    
    async def delete(self, post: Post):
        await self.db.delete(post)
        await self.db.commit()

    async def bulk_count(self, model, column, ids: list[int]):
        query = (
            select(column, func.count())
            .where(column.in_(ids))
            .group_by(column)
        )
        result = await self.db.execute(query)
        return {row[0]: row[1] for row in result.all()}