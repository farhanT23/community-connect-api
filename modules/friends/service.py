from fastapi import HTTPException
from . import repository
from ..user import repository as user_repository

class FriendService:
    def __init__(self,db):
        self.repository = repository
        self.user_repository = user_repository
        self.db = db
    
    def get_all_users(self,current_id:int|None=None):
        users = self.user_repository.get_all(self.db,current_id)
        return users
    
    async def toggle_follow(self,user_id,follower_id):
        if(user_id == follower_id):
            raise HTTPException(status_code=400,detail="You can not follow yourself")
        
        return await self.repository.toggle_follow(self.db,user_id,follower_id)

        
