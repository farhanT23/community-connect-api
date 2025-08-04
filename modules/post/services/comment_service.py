from sqlalchemy.ext.asyncio import AsyncSession
from modules.post.models import Comment
from modules.post.schema import CommentBase, CommentReplyOut, UserSummaryOut
from modules.post.repository.comment_repository import CommentRepository
from sqlalchemy import func


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
