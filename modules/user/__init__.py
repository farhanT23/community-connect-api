
from fastapi import APIRouter, BackgroundTasks,Request,Depends, Response,status
from sqlalchemy.ext.asyncio import AsyncSession


from middlewares.auth import get_current_user
from utils.send_email import send_mail as send_email
from utils.error_response import ErrorResponse
from utils.database import get_db

from .schema import (UserForgotPasswordSchema, UserLoginResponseSchema, UserLoginSchema, UserResetPasswordSchema, 
                     UserSchema,UserCreateSchema,Token,
                     UserProfileUpdateSchema

                     )
from .service import UserService

router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={
        404: {"model": ErrorResponse},
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        200: {"model": ErrorResponse},
        },
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

@router.post('/forget-password')
async def forget_password(request:Request,user:UserForgotPasswordSchema,background_tasks:BackgroundTasks,db:AsyncSession=Depends(get_db)):
    service = UserService(db)
    data = await service.forget_password(user)

    background_tasks.add_task(
            send_email,
            subject="Reset Password",
            recipients=[user.email],
            data={"token":data["token"],"user":data["user"]},
            template="reset_password.html"
        )
    
    return {"detail":"Email sent"}


@router.post('/reset-password/{token}')
async def reset_password(request:Request,token:str,reset_password:UserResetPasswordSchema,db:AsyncSession=Depends(get_db)):
    service = UserService(db)
    await service.reset_password(token,reset_password)

    return {"detail":"Password reseted Successfully"}