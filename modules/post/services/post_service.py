from typing import Optional, List
from fastapi import UploadFile, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from modules.post.models import Post, PrivacyEnum, Reaction, Comment
from modules.post.schema import PostOut, PostShareOut, UserSummaryOut, MediaOut
from modules.post.repository.post_repository import PostRepository
from modules.post.services.media_service import MediaService
from modules.user.models import User


class PostService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = PostRepository(db)
        self.media_service = MediaService(db)

    async def get_post_detail(self, post_id: int, current_user_id: Optional[int]) -> PostOut:
        row = await self.repository.get_post_with_details(post_id, current_user_id)
        if not row:
            return {"message": "Post not found"}

        if current_user_id:
            post, reaction_count, comment_count, share_count, reaction_type_value = row
        else:
            post, reaction_count, comment_count, share_count = row
            reaction_type_value = None

        if post.privacy == PrivacyEnum.ONLY_ME and post.user_id != current_user_id:
            return {"message": "You do not have permission to view this post"}

        return self._map_post_to_post_out(post, reaction_count, comment_count, share_count, reaction_type_value)

    async def create_post(
        self,
        user_id: int,
        content: Optional[str],
        privacy: PrivacyEnum,
        media_files: Optional[List[UploadFile]]
    ) -> PostOut:

        saved_media = await self.media_service.save_media_files(media_files)

        post = Post(
            user_id=user_id,
            content=content,
            privacy=privacy,
            tagged_media=saved_media
        )
        self.db.add(post)

        await self.db.commit()

        await self.db.refresh(post)

        user = await self.db.get(User, user_id)

        user_out = UserSummaryOut(
            id=user.id,
            name=user.name,
            profile_image=user.profile_image,
        )

        media_out = [
            MediaOut(id=m.id, file=m.file)
            for m in saved_media
        ]

        return PostOut(
            id=post.id,
            content=post.content,
            privacy=post.privacy,
            user=user_out,
            tagged_media=media_out,
            reaction_count=0,
            comment_count=0,
            share_count=0,
            created_at=post.created_at,
            updated_at=post.updated_at,
            original_post=None
        )

    async def delete_post(self, post_id: int, current_user_id: int):
        post = await self.repository.get_post_with_media(post_id)

        if not post:
            return {"message": "Post not found"}
        if post.user_id != current_user_id:
            return {"message": "You do not have permission to delete this post"}

        for media in post.tagged_media:
            # delete_media_file is synchronous, so no await is needed
            await self.media_service.delete_media_file(media)

        await self.repository.delete(post)

    async def edit_post(self, post_id: int, user_id: int, content: Optional[str], privacy: PrivacyEnum, media_files: Optional[List[UploadFile]]) -> PostOut:
        post = await self.repository.get_post_with_media(post_id)

        if not post:
            return {"message": "Post not found"}
        if post.user_id != user_id:
            return {"message": "You do not have permission to edit this post"}

        # Update content and privacy
        post.content = content
        post.privacy = privacy

        # Handle media files
        if media_files is not None:
            # Delete existing media files
            for media in post.tagged_media:
                await self.media_service.delete_media_file(media)
            # Clear the media association
            post.tagged_media.clear()
            # Save new media files
            saved_media = await self.media_service.save_media_files(media_files)
            post.tagged_media = saved_media

        await self.repository.update(post)

        return self._map_post_to_post_out(post, 0, 0, 0)

    async def get_user_posts(self, user_id: int, current_user_id: Optional[int], limit: int, offset: int) -> List[PostOut]:
        posts = await self.repository.get_user_posts(user_id, limit=limit, offset=offset)

        if not posts:
            return []

        post_ids = [post.id for post in posts]
        reaction_counts = await self.repository.bulk_count(Reaction, Reaction.post_id, post_ids)
        comment_counts = await self.repository.bulk_count(Comment, Comment.post_id, post_ids)
        share_counts = await self.repository.bulk_count(Post, Post.original_post_id, post_ids)

        user_reactions = {}
        if current_user_id:
            reaction_query = select(Reaction.post_id, Reaction.type).where(
                Reaction.user_id == current_user_id,
                Reaction.post_id.in_(post_ids)
            )
            reaction_result = await self.db.execute(reaction_query)
            user_reactions = {post_id: r_type for post_id, r_type in reaction_result.all()}

        return [
            self._map_post_to_post_out(
                post,
                reaction_counts.get(post.id, 0),
                comment_counts.get(post.id, 0),
                share_counts.get(post.id, 0),
                user_reactions.get(post.id)
            ) for post in posts
            if not (post.privacy == PrivacyEnum.ONLY_ME and post.user_id != current_user_id)
        ]

    def _map_post_to_post_out(self, post: Post, reaction_count: int, comment_count: int, share_count: int, reaction_type: Optional[str] = None) -> PostOut:
        # Use model_validate instead of the deprecated from_orm
        user_out = UserSummaryOut.model_validate(post.user)
        media_out = [MediaOut.model_validate(media) for media in post.tagged_media]

        original_post_out = None
        if post.original_post:
            original_user = UserSummaryOut.model_validate(post.original_post.user)
            original_media = [MediaOut.model_validate(media) for media in post.original_post.tagged_media]
            original_post_out = PostShareOut(
                id=post.original_post.id,
                content=post.original_post.content,
                privacy=post.original_post.privacy,
                user=original_user,
                tagged_media=original_media,
                created_at=post.original_post.created_at,
                updated_at=post.original_post.updated_at,
            )

        reaction_type_value = None
        if reaction_type:
            if hasattr(reaction_type, 'value'):
                reaction_type_value = reaction_type.value
            else:
                reaction_type_value = reaction_type

        return PostOut(
            id=post.id,
            user=user_out,
            content=post.content,
            privacy=post.privacy,
            tagged_media=media_out,
            reaction_count=reaction_count,
            comment_count=comment_count,
            share_count=share_count,
            reaction_type=reaction_type_value,
            created_at=post.created_at,
            updated_at=post.updated_at,
            original_post=original_post_out,
        )

    async def _count(self, model, *filters):
        query = select(func.count()).select_from(model).filter(*filters)
        result = await self.db.execute(query)
        return result.scalar_one()

    async def share_post(self, post_id: int, user_id: int) -> PostOut:
        query = (
            select(Post)
            .options(
                selectinload(Post.user),
                selectinload(Post.tagged_media)
            )
            .where(Post.id == post_id)
        )
        result = await self.db.execute(query)
        original_post = result.scalar_one_or_none()

        if not original_post:
            raise HTTPException(status_code=404, detail="Original post not found")

        if original_post.privacy != PrivacyEnum.PUBLIC:
            raise HTTPException(status_code=403, detail="Only public posts can be shared")

        shared_post = Post(
            user_id=user_id,
            original_post_id=original_post.id,
            content="shared post",
            privacy=PrivacyEnum.PUBLIC
        )

        self.db.add(shared_post)
        await self.db.commit()
        await self.db.refresh(shared_post)

        reaction_count = 0
        comment_count = 0
        share_count = await self._count(Post, Post.original_post_id == original_post.id)

        user = await self.db.get(User, user_id)
        user_out = UserSummaryOut(
            id=user.id,
            name=user.name,
            profile_image=user.profile_image,
        )

        original_user_out = UserSummaryOut(
            id=original_post.user.id,
            name=original_post.user.name,
            profile_image=original_post.user.profile_image,
        )

        original_media = [
            MediaOut(id=m.id, file=m.file)
            for m in original_post.tagged_media
        ]

        original_post_out = PostShareOut(
            id=original_post.id,
            content=original_post.content,
            privacy=original_post.privacy,
            user=original_user_out,
            tagged_media=original_media,
            created_at=original_post.created_at,
            updated_at=original_post.updated_at,
        )

        return PostOut(
            id=shared_post.id,
            user=user_out,
            content=shared_post.content,
            privacy=shared_post.privacy,
            tagged_media=[],
            reaction_count=reaction_count,
            comment_count=comment_count,
            share_count=share_count,
            created_at=shared_post.created_at,
            updated_at=shared_post.updated_at,
            original_post=original_post_out
        )



