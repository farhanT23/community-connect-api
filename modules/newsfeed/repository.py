from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from sqlalchemy.sql import exists
from sqlalchemy.orm import aliased

from modules.post.models import Post, PrivacyEnum, Reaction, Comment
from modules.friends.models import Friends

class NewsfeedRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_newsfeed(self, user_id: int = None, page: int = 1, page_size: int = 10):
        reaction_count_subquery = (
            select(func.count(Reaction.id))
            .where(Reaction.post_id == Post.id)
            .correlate(Post)
            .scalar_subquery()
        )

        comment_count_subquery = (
            select(func.count(Comment.id))
            .where(Comment.post_id == Post.id)
            .correlate(Post)
            .scalar_subquery()
        )

        SharedPost = aliased(Post)
        share_count_subquery = (
            select(func.count(SharedPost.id))
            .where(SharedPost.original_post_id == Post.id)
            .correlate(Post)
            .scalar_subquery()
        )

        query = (
            select(
                Post,
                reaction_count_subquery.label("reaction_count"),
                comment_count_subquery.label("comment_count"),
                share_count_subquery.label("share_count"),
            )
            .options(
                selectinload(Post.user),
                selectinload(Post.tagged_media),
                selectinload(Post.original_post).selectinload(Post.user),
                selectinload(Post.original_post).selectinload(Post.tagged_media),
            )
        )

        if user_id:
            following_subquery = (
                select(Friends.friend_id)
                .where(Friends.user_id == user_id)
                .scalar_subquery()
            )
            query = query.where(
                or_(
                    Post.privacy == PrivacyEnum.PUBLIC,
                    Post.user_id == user_id,
                    Post.user_id.in_(following_subquery),
                )
            )
        else:
            query = query.where(Post.privacy == PrivacyEnum.PUBLIC)

        query = query.order_by(func.random()).limit(page_size).offset((page - 1) * page_size)

        result = await self.db.execute(query)

        posts = []
        for row in result.all():
            post, reaction_count, comment_count, share_count = row
            post.reaction_count = reaction_count
            post.comment_count = comment_count
            post.share_count = share_count
            posts.append(post)

        return posts
