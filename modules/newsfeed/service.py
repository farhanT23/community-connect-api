from sqlalchemy.ext.asyncio import AsyncSession
from modules.newsfeed.repository import NewsfeedRepository

class NewsfeedService:
    def __init__(self, db: AsyncSession):
        self.repository = NewsfeedRepository(db)

    async def get_newsfeed(self, user_id: int = None, page: int = 1, page_size: int = 10):
        return await self.repository.get_newsfeed(user_id, page, page_size)
