from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from modules.post.models import Reaction, Post

class ReactionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_post_by_id(self, post_id: int):
        result = await self.db.get(Post, post_id)
        return result

    async def find_user_reaction_for_post(self, user_id: int, post_id: int):
        query = select(Reaction).where(Reaction.post_id == post_id).where(Reaction.user_id == user_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def add(self, reaction: Reaction):
        self.db.add(reaction)
        await self.db.commit()
    
    async def delete(self, reaction: Reaction):
        await self.db.delete(reaction)
        await self.db.commit()

    async def save(self):
        await self.db.commit()