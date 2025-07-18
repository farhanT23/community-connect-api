from sqlalchemy.ext.asyncio import AsyncSession

from typing import Optional
from sqlalchemy import delete, select
from modules.post.models import Comment, Post
from sqlalchemy.orm import selectinload


class CommentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_post_by_id(self, post_id: int):
        result = await self.db.execute(
            select(Post).where(Post.id == post_id)
        )
        return result.scalar_one_or_none()
    
    async def add_and_refresh(self, comment: Comment):
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        return comment
    
    async def get_comment_with_user_by_id(self, comment_id: int):
        query = select(Comment).options(
            selectinload(Comment.user)
        ).where(Comment.id == comment_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_comment_by_id(self, comment_id: int):
        result = await self.db.get(Comment, comment_id)
        return result
    
    async def get_replies_for_comment(self, comment_id: int):
        query = select(Comment).where(
            Comment.parent_id == comment_id
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def delete_many_comments(self, comment_ids: list[int]):
        await self.db.execute(
            delete(Comment).where(Comment.id.in_(comment_ids))
        )
        await self.db.commit()
        
        