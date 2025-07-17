from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, ConfigDict

from modules.user.schema import UserSummaryOut


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
    file: str

    model_config = {"from_attributes": True}

class PostBaseOut(BaseModel):
    id: int
    content: Optional[str]
    privacy: PrivacyEnum
    user: UserSummaryOut
    tagged_media: List[MediaOut]

    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class PostOut(PostBaseOut):
    reaction_count: int
    comment_count: int
    share_count: int
    reaction_type: Optional[ReactionTypeEnum] = None
    original_post: Optional[PostShareOut] = None

class PostShareOut(PostBaseOut):
    pass

class PostCreate(BaseModel):
    content: Optional[str] = None
    privacy: PrivacyEnum = PrivacyEnum.public