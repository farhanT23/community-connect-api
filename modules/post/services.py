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
        saved_media = await self.upload_media_files(media_files)

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

        query = (
            select(Post)
            .where(Post.id == post_id)
            .options(selectinload(Post.tagged_media))
        )
        result = await self.db.execute(query)
        post = result.scalar_one_or_none()


        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        if post.user_id != current_user_id:
            raise HTTPException(status_code=403, detail="You are not allowed to delete this post")

        for media in post.tagged_media:
            file_path = os.path.join("media", media.file)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Warning: Failed to delete {file_path}. Error: {e}")

        await self.db.delete(post)

        await self.db.commit()

    async def upload_media_files(self, media_files: Optional[List[UploadFile]]) -> List[Media]:
        saved_media = []
        media_dir = "media"
        os.makedirs(media_dir, exist_ok=True)

        for file in media_files or []:
            filename = self._generate_unique_filename(file.filename)
            file_path = os.path.join(media_dir, filename)

            # Save to disk
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())

            # Save to DB
            media = Media(
                file=filename,
                media_type=file.content_type
            )
            self.db.add(media)
            await self.db.flush()  # So media.id is populated

            saved_media.append(media)

        return saved_media

    async def edit_post(
            self,
            post_id: int,
            user_id: int,
            content: Optional[str],
            privacy: PrivacyEnum,
            media_files: Optional[List[UploadFile]]
    ) -> PostOut:
        # 1. Fetch the post
        query = (
            select(Post)
            .where(Post.id == post_id)
            .options(selectinload(Post.tagged_media), selectinload(Post.user))
        )
        result = await self.db.execute(query)
        post = result.scalar_one_or_none()

        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # 2. Check if the user is the owner
        if post.user_id != user_id:
            raise HTTPException(status_code=403, detail="You are not allowed to edit this post")

        # 3. Update fields
        post.content = content
        post.privacy = privacy

        # 4. Add new media files if any
        new_media = await self.upload_media_files(media_files)
        post.tagged_media.extend(new_media)

        # 5. Save
        await self.db.commit()
        await self.db.refresh(post)

        # 6. Build response
        reaction_count = await self._count(Reaction, Reaction.post_id == post.id)
        comment_count = await self._count(Comment, Comment.post_id == post.id)
        share_count = await self._count(Post, Post.original_post_id == post.id)

        return PostOut(
            id=post.id,
            content=post.content,
            privacy=post.privacy,
            user=UserSummaryOut(
                id=post.user.id,
                name=post.user.name,
                profile_image=post.user.profile_image
            ),
            tagged_media=[
                MediaOut(id=m.id, file=m.file)
                for m in post.tagged_media
            ],
            reaction_count=reaction_count,
            comment_count=comment_count,
            share_count=share_count,
            created_at=post.created_at,
            updated_at=post.updated_at,
            original_post=None  # not needed for edit
        )

    async def remove_post_media(self, post_id: int, media_id: int, user_id: int):
        # 1. Get post with media relation
        query = (
            select(Post)
            .where(Post.id == post_id)
            .options(selectinload(Post.tagged_media))
        )
        result = await self.db.execute(query)
        post = result.scalar_one_or_none()

        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        if post.user_id != user_id:
            raise HTTPException(status_code=403, detail="You are not allowed to remove media from this post")

        # 2. Find the media in post
        media_to_remove = next((m for m in post.tagged_media if m.id == media_id), None)
        if not media_to_remove:
            raise HTTPException(status_code=404, detail="Media not attached to this post")

        # 3. Remove file from disk
        file_path = os.path.join("media", media_to_remove.file)
        if os.path.exists(file_path):
            os.remove(file_path)

        # 4. Detach from post
        post.tagged_media.remove(media_to_remove)

        # 5. Optional: check if media used elsewhere, delete if not
        # We do this only if it's orphaned from all posts
        media_used_elsewhere = (
            select(Post)
            .join(Post.tagged_media)
            .where(Media.id == media_id)
            .where(Post.id != post_id)
        )
        other_use = await self.db.execute(media_used_elsewhere)
        if not other_use.first():
            await self.db.delete(media_to_remove)

        # 6. Save changes
        await self.db.commit()

    def _generate_unique_filename(self, original_filename: str) -> str:
        ext = os.path.splitext(original_filename)[1]
        return f"{uuid.uuid4().hex}{ext}"

    async def _count(self, model, *filters):
        query = select(func.count()).select_from(model).filter(*filters)
        result = await self.db.execute(query)
        return result.scalar_one()
