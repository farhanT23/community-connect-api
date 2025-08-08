from pydantic import BaseModel
from typing import List
from modules.post.schema import PostOut

class NewsFeedResponse(BaseModel):
    posts: List[PostOut]
