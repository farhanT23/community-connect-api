import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
# These will be properly implemented in the next step
from modules.user import repository as user_repository
from modules.post.repository.post_repository import PostRepository
from .schema import SearchResultsSchema, SearchTabEnum

class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.post_repository = PostRepository(db)

    async def perform_search(self, query: str, tab: SearchTabEnum) -> SearchResultsSchema:
        if tab == SearchTabEnum.users:
            users = await user_repository.get_all_user_by_name_alike(self.db, query)
            
            if not users:
                return {"message": "No user found"}
            
            return SearchResultsSchema(users=users, posts=[])

        elif tab == SearchTabEnum.posts:
            posts = await self.post_repository.search_public_posts_by_content(query)

            if not posts:
                return {"message": "No post found"}
            
            return SearchResultsSchema(users=[], posts=posts)
        
        users = await user_repository.get_all_user_by_name_alike(self.db, query)
        posts = await self.post_repository.search_public_posts_by_content(query)
        return SearchResultsSchema(users=users, posts=posts)