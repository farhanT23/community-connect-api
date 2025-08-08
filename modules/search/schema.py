from enum import Enum
from pydantic import BaseModel
from typing import List, Optional
from modules.user.schema import UserSummaryOut
from modules.post.schema import PostOut

class SearchTabEnum(str, Enum):
    all = "all"
    users = "users"
    posts = "posts"

class SearchResultsSchema(BaseModel):
    users: Optional[List[UserSummaryOut]] = []
    posts: Optional[List[PostOut]] = []