from enum import Enum
from pydantic import BaseModel
from typing import List, Optional
from modules.user.schema import UserSchema
from modules.post.schema import PostBaseOut

class SearchTabEnum(str, Enum):
    all = "all"
    users = "users"
    posts = "posts"

class SearchResultsSchema(BaseModel):
    users: Optional[List[UserSchema]] = []
    posts: Optional[List[PostBaseOut]] = []