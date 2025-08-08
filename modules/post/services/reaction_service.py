from sqlalchemy.ext.asyncio import AsyncSession
from modules.post.models import Reaction
from modules.post.schema import ReactionTypeEnum
from modules.post.repository.reaction_repository import ReactionRepository

class ReactionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = ReactionRepository(db)

    async def react_to_post(
            self,
            post_id: int,
            user_id: int,
            reaction_type: ReactionTypeEnum
    ):
        post = await self.repository.get_post_by_id(post_id)

        if not post:
            raise ValueError("Post not found")
        
        existing_reaction = await self.repository.find_user_reaction_for_post(user_id, post_id)

        if existing_reaction:
            if existing_reaction.type == reaction_type:
                await self.repository.delete(existing_reaction)
                return {"detail": "Reaction removed"}
            else:
                existing_reaction.type = reaction_type
                await self.repository.save()
                return {"detail": "Reaction updated"}
        else:
            new_reaction = Reaction(
                post_id=post_id,
                user_id=user_id,
                type=reaction_type.value
            )
            await self.repository.add(new_reaction)
            return {"detail": "Reaction added"}