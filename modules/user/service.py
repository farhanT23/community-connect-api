
from fastapi import HTTPException
from utils.hasher import Hasher

from . import repository

class UserService:
    def __init__(self,db):
        self.repository = repository
        self.db = db
    async def check_user_exist(self,email):
        user = await self.repository.get_by_email(self.db,email)
        return user
    
    async def create_user(self,user):
        is_email_exist = await self.check_user_exist(user.email)
        if is_email_exist:
            raise HTTPException(status_code=400,detail="User already exist")
        
        user.password = Hasher.hash(user.password)
        
        user = self.repository.create_object(user)
        
        return await self.repository.create(self.db,user)
        
        