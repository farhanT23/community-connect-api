from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel


class PrivacyEnum(str, Enum):
    public = "public"
    follower = "follower"
    only_me = "only_me"


class ReactionTypeEnum(str, Enum):
    like = "like"
    love = "love"
    haha = "haha"
    wow = "wow"
    sad = "sad"
    angry = "angry"


class MediaOut(BaseModel):
    id: int
    file_path: str
    media_type: Optional[str] = "image"

    model_config = {"from_attributes": True}


class CommentBase(BaseModel):
    content: str
    parent_id: Optional[int] = None


class CommentCreate(CommentBase):
    pass


class CommentOut(BaseModel):
    id: int
    user_id: int
    content: str
    parent_id: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    replies: List[CommentOut] = []  # 👈 recursion works via future annotations

    model_config = {"from_attributes": True}


class ReactionOut(BaseModel):
    id: int
    user_id: int
    type: ReactionTypeEnum

    model_config = {"from_attributes": True}


class PostBase(BaseModel):
    content: Optional[str] = None
    privacy: PrivacyEnum = PrivacyEnum.public
    original_post_id: Optional[int] = None
    tagged_media_ids: Optional[List[int]] = []


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    content: Optional[str] = None
    privacy: Optional[PrivacyEnum] = None
    tagged_media_ids: Optional[List[int]] = None


class PostOut(BaseModel):
    id: int
    user_id: int
    content: Optional[str]
    privacy: PrivacyEnum
    original_post_id: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    tagged_media: List[MediaOut] = []
    comments: List[CommentOut] = []
    reactions: List[ReactionOut] = []

    model_config = {"from_attributes": True}
