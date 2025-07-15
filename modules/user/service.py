
from datetime import datetime, timezone
from fastapi import HTTPException
from utils.hasher import Hasher
from utils.jwt_token import JWTToken

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
        
        try:
            user = await self.repository.create(self.db,user)
        except Exception as e:
            raise HTTPException(status_code=400,detail=str(e))
        return user
    
    async def login(self,userRequest):
        user = await self.repository.get_by_email(self.db,userRequest.email)
        if not user or not user.is_active or not Hasher.verify(userRequest.password,user.password):
            raise HTTPException(status_code=400,detail="Invalid email or password")

        return user
    
    async def genarate_token(self,user):
        data = {}
        data['user_id'] = user.id
        data['email'] = user.email

        token = JWTToken.create_access_token(data)

        return token
    
    async def refresh_token(self,user):
        data = {}
        data['user_id'] = user.id

        token = JWTToken.create_refresh_token(data)

        return token
        

    async def get_user(self,user_id):
        user = await self.repository.get_by_id(self.db,user_id)
        if not user:
            raise HTTPException(status_code=404,detail="User not found")
        
        return user
    
    async def get_refresh_token_user(self,token):
        payload = JWTToken.decode_token(token)

        if not payload:
            raise HTTPException(
            status_code=404,
            detail="Invalid or expired token",
        )

        user = await self.repository.get_by_id(self.db,payload['user_id'])

        if not user:
            raise HTTPException(status_code=404,detail="User not found")

        return user
        
    async def update_profile(self,user_id,profile):
        user = await self.repository.get_by_id(self.db,user_id)
        user.birthdate = profile.birthdate
        user.gender = profile.gender
        user.bio = profile.bio
        try:
            user = await self.repository.update(self.db,user)
        except Exception as e:
            raise HTTPException(status_code=400,detail=str(e))
        return user
    
