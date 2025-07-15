
from fastapi import APIRouter,Request,Depends, Response,status
from sqlalchemy.ext.asyncio import AsyncSession


from middlewares.auth import get_current_user
from utils.error_response import ErrorResponse
from utils.database import get_db

from .schema import (UserLoginResponseSchema, UserLoginSchema, 
                     UserSchema,UserCreateSchema,Token,
                     UserProfileUpdateSchema

                     )
from .service import UserService

router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"model": ErrorResponse},400: {"model": ErrorResponse},401: {"model": ErrorResponse}},
)



@router.get("/health")
async def health():
    return {"message": "Up"}


@router.post('/',response_model=UserLoginResponseSchema,status_code=status.HTTP_201_CREATED)
async def create_user(request:Request,user:UserCreateSchema,db:AsyncSession=Depends(get_db)):

    service = UserService(db)
    user = await service.create_user(user)
    response = UserLoginResponseSchema(
            user=user,
            token=Token(
                access_token=await service.genarate_token(user),
                refresh_token=await service.refresh_token(user)
            )
        )

    return response


@router.post('/login',response_model=UserLoginResponseSchema)
async def login(request:Request,response:Response,user:UserLoginSchema,db:AsyncSession=Depends(get_db)):

    service = UserService(db)
    user = await service.login(user)
    token_response = UserLoginResponseSchema(
            user=user,
            token=Token(
                access_token=await service.genarate_token(user),
                refresh_token=await service.refresh_token(user)
            )
        )

    
    return token_response

@router.get('/me',response_model=UserSchema,)
async def get_user(
    request:Request,
    db:AsyncSession=Depends(get_db),
    current_user:dict=Depends(get_current_user)
    ):
    user_service = UserService(db)

    user = await user_service.get_user(current_user["user_id"])

    return user

@router.post('/refresh-token',response_model=Token)
async def refresh_token(request:Request,token:str,db:AsyncSession=Depends(get_db)):


    service = UserService(db)
    user = await service.get_refresh_token_user(token)
    token_response =Token(
        access_token=await service.genarate_token(user),
        refresh_token=await service.refresh_token(user)
    )

    
    return token_response

@router.put('/profile',response_model=UserProfileUpdateSchema)
async def update_profile(request:Request,profile:UserProfileUpdateSchema
                         ,db:AsyncSession=Depends(get_db),
                         current_user:dict=Depends(get_current_user)):

    service = UserService(db)
    user = await service.update_profile(current_user["user_id"],profile)

    return user