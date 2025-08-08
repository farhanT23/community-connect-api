from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from modules.post.models import Comment
from modules.post.schema import CommentBase, CommentReplyOut, UserSummaryOut, CommentOut
from modules.post.repository.comment_repository import CommentRepository
from sqlalchemy import func, select

from modules.user.models import User


class CommentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = CommentRepository(db)

    async def create_comment(self, post_id: int, content: str, user_id: int):
        post = await self.repository.get_post_by_id(post_id)

        if not post:
            raise ValueError("Post not found")
        
        new_comment = Comment(
            post_id=post_id,
            user_id=user_id,
            content=content,
            created_at=func.now(),
            updated_at=func.now()
        )

        await self.repository.add_and_refresh(new_comment)

        comment_with_user = await self.repository.get_comment_with_user_by_id(new_comment.id)

        return self.map_comment_to_schema(comment_with_user, CommentBase)

    async def create_reply(self, post_id: int, content: str, user_id: int, comment_id: int):
        parent_comment = await self.repository.get_comment_by_id(comment_id)

        if not parent_comment:
            raise ValueError("Parent comment not found")
        
        if parent_comment.post_id != post_id:
            raise ValueError("Parent comment does not belong to the specified post")
        
        if parent_comment.parent_id is not None:
            raise ValueError("Cannot reply to a reply")
        
        reply = Comment(
            post_id=post_id,
            user_id=user_id,
            content=content,
            parent_id=parent_comment.id,
            created_at=func.now(),
            updated_at=func.now()
        )

        await self.repository.add_and_refresh(reply)

        reply_with_user = await self.repository.get_comment_with_user_by_id(reply.id)

        return self.map_comment_to_schema(reply_with_user, CommentReplyOut)
    
    async def delete_comment(self, comment_id: int, user_id: int):
        comment = await self.repository.get_comment_by_id(comment_id)

        if not comment:
            raise ValueError("Comment not found")
        
        if comment.user_id != user_id:
            raise PermissionError("You do not have permission to delete this comment")
        
        if comment.parent_id is None:
            replies = await self.repository.get_replies_for_comment(comment_id)
            reply_ids = [reply.id for reply in replies]
            await self.repository.delete_many_comments(reply_ids)

        await self.db.delete(comment)
        await self.db.commit()
        return {"message": "Comment deleted successfully"}

    async def get_post_comments(
            self,
            post_id: int,
            user_id: Optional[int] = None,
            limit: int = 10,
            offset: int = 0
    ):
        parent_comments_query = (
            select(Comment, User)
            .join(User, Comment.user_id == User.id)
            .where(Comment.post_id == post_id, Comment.parent_id.is_(None))
            .order_by(Comment.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        parent_comments_result = await self.db.execute(parent_comments_query)
        parent_comments_data = parent_comments_result.all()

        if not parent_comments_data:
            return []

        # Extract parent comment IDs for replies query
        parent_comment_ids = [comment.id for comment, user in parent_comments_data]

        # Query to get all replies for the parent comments with user info
        replies_query = (
            select(Comment, User)
            .join(User, Comment.user_id == User.id)
            .where(Comment.parent_id.in_(parent_comment_ids))
            .order_by(Comment.created_at.asc())
        )

        replies_result = await self.db.execute(replies_query)
        replies_data = replies_result.all()

        # Group replies by parent_id
        replies_by_parent = {}
        for reply, reply_user in replies_data:
            if reply.parent_id not in replies_by_parent:
                replies_by_parent[reply.parent_id] = []
            replies_by_parent[reply.parent_id].append({
                "id": reply.id,
                "content": reply.content,
                "user": {
                    "id": reply_user.id,
                    "name": reply_user.name,
                    "profile_image": reply_user.profile_image
                },
                "created_at": reply.created_at,
                "updated_at": reply.updated_at,
                "parent_id": reply.parent_id
            })

        # Build the final response
        result = []
        for comment, comment_user in parent_comments_data:
            comment_dict = {
                "id": comment.id,
                "content": comment.content,
                "user": {
                    "id": comment_user.id,
                    "name": comment_user.name,
                    "profile_image": comment_user.profile_image
                },
                "created_at": comment.created_at,
                "updated_at": comment.updated_at,
                "replies": replies_by_parent.get(comment.id, [])
            }
            result.append(comment_dict)

        return result






    def map_comment_to_schema(self, comment: Comment, schema_class):
        user_summary = UserSummaryOut(
            id=comment.user.id,
            name=comment.user.name,
            profile_image=comment.user.profile_image
        )

        data = {
            "id": comment.id,
            "content": comment.content,
            "user": user_summary,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
        }

        if issubclass(schema_class, CommentReplyOut):
            data['parent_id'] = comment.parent_id

        return schema_class(**data)
