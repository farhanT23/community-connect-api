# modules/post/service.py
import os
import uuid
from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, UploadFile

from modules.post.models import Post, Reaction, Comment, Media
from modules.post.schema import PostOut, PostShareOut, UserSummaryOut, MediaOut, PrivacyEnum
from modules.user.models import User
from modules.post.models import Post, Reaction, Comment, PrivacyEnum
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

        if post.privacy == PrivacyEnum.ONLY_ME:
            if not current_user_id or (current_user_id != post.user_id):
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

    async def create_post(
        self,
        user_id: int,
        content: Optional[str],
        privacy: PrivacyEnum,
        media_files: Optional[List[UploadFile]]
    ) -> PostOut:
        # Step 1: Save each media file to disk and record in DB
        saved_media = []

        media_dir = "media"
        os.makedirs(media_dir, exist_ok=True)

        for file in media_files or []:  # handle None
            filename = self._generate_unique_filename(file.filename)
            file_path = os.path.join(media_dir, filename)

            # Save to disk
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())

            # Create Media row
            media = Media(
                file=filename,
                media_type=file.content_type
            )
            self.db.add(media)
            await self.db.flush()  # Needed to get media.id
            saved_media.append(media)

        # Step 2: Create Post with media
        post = Post(
            user_id=user_id,
            content=content,
            privacy=privacy,
            tagged_media=saved_media
        )
        self.db.add(post)

        # Step 3: Commit all changes
        await self.db.commit()

        # Step 4: Refresh post from DB
        await self.db.refresh(post)

        # Step 5: Build user object for response
        user = await self.db.get(User, user_id)

        user_out = UserSummaryOut(
            id=user.id,
            name=user.name,
            profile_image=user.profile_image,
        )

        # Step 6: Build media list for response
        media_out = [
            MediaOut(id=m.id, file=m.file, media_type=m.media_type)
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


    def _generate_unique_filename(self, original_filename: str) -> str:
        ext = os.path.splitext(original_filename)[1]
        return f"{uuid.uuid4().hex}{ext}"

    async def _count(self, model, *filters):
        query = select(func.count()).select_from(model).filter(*filters)
        result = await self.db.execute(query)
        return result.scalar_one()
