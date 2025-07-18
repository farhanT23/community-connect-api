import os
import uuid
from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, aliased
from fastapi import HTTPException, UploadFile

from modules.post import CommentReplyOut
from modules.post.models import Post, Reaction, Comment, Media
from modules.post.schema import PostOut, PostShareOut, UserSummaryOut, MediaOut, PrivacyEnum, ReactionTypeEnum, CommentBase
from modules.user.models import User
from modules.post.models import Post, Reaction, Comment, PrivacyEnum
from modules.post.schema import PostOut, PostShareOut, UserSummaryOut, MediaOut


class PostService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_post_detail(self, post_id: int, current_user_id: Optional[int]) -> PostOut:
        # Aliased Post for share count subquery
        P2 = aliased(Post)

        # Define correlated subqueries for counts and user's reaction
        reaction_count_sub = select(func.count(Reaction.id)).where(Reaction.post_id == Post.id).scalar_subquery()
        comment_count_sub = select(func.count(Comment.id)).where(Comment.post_id == Post.id).scalar_subquery()
        share_count_sub = select(func.count(P2.id)).where(P2.original_post_id == Post.id).scalar_subquery()

        # Base query for the post, its relationships, and the counts
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

        # Conditionally add subquery for the current user's reaction
        if current_user_id:
            user_reaction_sub = (
                select(Reaction.type)
                .where((Reaction.post_id == Post.id) & (Reaction.user_id == current_user_id))
                .scalar_subquery()
            )
            query = query.add_columns(user_reaction_sub.label("reaction_type"))

        result = await self.db.execute(query)
        row = result.one_or_none()

        if not row:
            raise HTTPException(status_code=404, detail="Post not found")

        # Unpack results from the single row tuple
        if current_user_id:
            post, reaction_count, comment_count, share_count, reaction_type_value = row
        else:
            post, reaction_count, comment_count, share_count = row
            reaction_type_value = None

        if post.privacy == PrivacyEnum.ONLY_ME:
            if not current_user_id or (current_user_id != post.user_id):
                raise HTTPException(status_code=403, detail="This post is private")

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

        reaction_type = None
        if reaction_type_value:
            try:
                reaction_type = reaction_type_value.value
            except (ValueError, AttributeError):
                reaction_type = None
                
        return PostOut(
            id=post.id,
            user=user_out,
            content=post.content,
            privacy=post.privacy,
            tagged_media=media_out,
            reaction_count=reaction_count,
            comment_count=comment_count,
            share_count=share_count,
            reaction_type=reaction_type,
            created_at=post.created_at,
            updated_at=post.updated_at,
            original_post=original_post_out,
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

    async def react_to_post(
            self,
            post_id: int,
            user_id: int,
            reaction_type: ReactionTypeEnum
    ):

        post_query = select(Post).where(Post.id == post_id)
        result = await self.db.execute(post_query)
        post = result.scalar_one_or_none()

        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        reaction_query = (
            select(Reaction)
            .where(Reaction.post_id == post_id)
            .where(Reaction.user_id == user_id)
        )
        reaction_result = await self.db.execute(reaction_query)
        existing_reaction = reaction_result.scalar_one_or_none()

        if existing_reaction:
            if existing_reaction.type.value == reaction_type.value:
                await self.db.delete(existing_reaction)
                await self.db.commit()
                return {"detail": "Reaction removed"}
            else:
                existing_reaction.type = reaction_type.value
                await self.db.commit()
                return {"detail": "Reaction updated"}
        else:
            new_reaction = Reaction(
                post_id=post_id,
                user_id=user_id,
                type=reaction_type.value
            )
            self.db.add(new_reaction)
            await self.db.commit()
            return {"detail": "Reaction added"}

    def _generate_unique_filename(self, original_filename: str) -> str:
        ext = os.path.splitext(original_filename)[1]
        return f"{uuid.uuid4().hex}{ext}"

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

    async def comment_on_post(self, post_id: int, content: str, user_id: int):
        query = select(Post).where(Post.id == post_id)
        result = await self.db.execute(query)
        post = result.scalar_one_or_none()

        if not post:
            raise HTTPException(status_code=404, detail="Post not found")


        comment = Comment(
            post_id=post_id,
            user_id=user_id,
            content=content,
            created_at=func.now(),
            updated_at=func.now()
        )

        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)


        query = select(Comment).options(selectinload(Comment.user)).where(Comment.id == comment.id)
        result = await self.db.execute(query)
        comment_with_user = result.scalar_one()

        return CommentBase(
            id=comment_with_user.id,
            content=comment_with_user.content,
            user=UserSummaryOut(
                id=comment_with_user.user.id,
                name=comment_with_user.user.name,
                profile_image=comment_with_user.user.profile_image
            ),
            created_at=comment_with_user.created_at,
            updated_at=comment_with_user.updated_at
        )

    async def comment_reply(self, post_id: int, content: str, user_id: int, comment_id: int):
        # 1. Fetch the parent comment
        query = select(Comment).where(Comment.id == comment_id)
        result = await self.db.execute(query)
        parent_comment = result.scalar_one_or_none()

        if not parent_comment:
            raise HTTPException(status_code=404, detail="Parent comment not found")

        if parent_comment.post_id != post_id:
            raise HTTPException(status_code=400, detail="Comment does not belong to this post")

        if parent_comment.parent_id is not None:
            raise HTTPException(status_code=400, detail="Replies to replies are not allowed")

        reply = Comment(
            post_id=post_id,
            user_id=user_id,
            content=content,
            parent_id=parent_comment.id,
            created_at=func.now(),
            updated_at=func.now()
        )

        self.db.add(reply)
        await self.db.commit()
        await self.db.refresh(reply)

        query = select(Comment).options(selectinload(Comment.user)).where(Comment.id == reply.id)
        result = await self.db.execute(query)
        reply_with_user = result.scalar_one()

        return CommentReplyOut(
            id=reply_with_user.id,
            content=reply_with_user.content,
            parent_id=reply_with_user.parent_id,
            user=UserSummaryOut(
                id=reply_with_user.user.id,
                name=reply_with_user.user.name,
                profile_image=reply_with_user.user.profile_image
            ),
            created_at=reply_with_user.created_at,
            updated_at=reply_with_user.updated_at
        )

    async def delete_comment(self, comment_id: int, user_id: int):
        query = select(Comment).where(Comment.id == comment_id)
        result = await self.db.execute(query)
        comment = result.scalar_one_or_none()

        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        if comment.user_id != user_id:
            raise HTTPException(status_code=403, detail="You are not allowed to delete this comment")

        # Delete the comment where parent_id is comment_id
        reply_query = select(Comment).where(Comment.parent_id == comment_id)
        reply_result = await self.db.execute(reply_query)
        replies = reply_result.scalars().all()
        for reply in replies:
            await self.db.delete(reply)

        await self.db.delete(comment)
        await self.db.commit()

        # Return a 204 No Content response with detail
        return {"detail": "Comment deleted successfully"}

    async def get_user_posts(self, user_id: int, current_user_id: Optional[int], limit: int, offset: int):

        query = (
            select(Post)
            .where(Post.user_id == user_id)
            .options(
                selectinload(Post.user),
                selectinload(Post.tagged_media),
                selectinload(Post.original_post).selectinload(Post.user),
                selectinload(Post.original_post).selectinload(Post.tagged_media),
            )
            .order_by(Post.created_at.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        posts = result.scalars().all()

        if not posts:
            return []
        
        post_ids = [post.id for post in posts]


        reaction_counts= await self.bulk_count(Reaction, Reaction.post_id, post_ids)
        comment_counts = await self.bulk_count(Comment, Comment.post_id, post_ids)
        share_counts = await self.bulk_count(Post, Post.original_post_id, post_ids)

        user_reactions = {}
        if current_user_id:
            reaction_query = (
                select(Reaction.post_id, Reaction.type)
                .where(Reaction.user_id == current_user_id, Reaction.post_id.in_(post_ids))
            )
            reaction_result = await self.db.execute(reaction_query)
            for post_id, reaction_type in reaction_result.all():
                user_reactions[post_id] = reaction_type.value

        post_out_list = []
        for post in posts:
            if post.privacy == PrivacyEnum.ONLY_ME and post.user_id != current_user_id:
                continue

            
            user_out = UserSummaryOut(
                id=post.user.id,
                name=post.user.name,
                profile_image=post.user.profile_image,
            )

            media_out = [MediaOut(id=m.id, file=m.file) for m in post.tagged_media]

            original_post_out = None
            if post.original_post:
                original_user = UserSummaryOut(
                    id=post.original_post.user.id,
                    name=post.original_post.user.name,
                    profile_image=post.original_post.user.profile_image,
                )
                original_media = [
                    MediaOut(id=m.id, file=m.file) for m in post.original_post.tagged_media
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

            post_out = PostOut(
                id=post.id,
                user=user_out,
                content=post.content,
                privacy=post.privacy,
                tagged_media=media_out,
                reaction_count=reaction_counts.get(post.id, 0),
                comment_count=comment_counts.get(post.id, 0),
                share_count=share_counts.get(post.id, 0),
                reaction_type=user_reactions.get(post.id),
                created_at=post.created_at,
                updated_at=post.updated_at,
                original_post=original_post_out,
            )
            post_out_list.append(post_out)

        return post_out_list
        
    async def bulk_count(self, model, column, ids: list[int]) -> dict[int, int]:
        query = (
            select(column, func.count())
            .where(column.in_(ids))
            .group_by(column)
        )
        result = await self.db.execute(query)
        return {row[0]: row[1] for row in result.all()}
        

        

