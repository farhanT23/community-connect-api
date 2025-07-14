
from fastapi import APIRouter,Request,Depends
from sqlalchemy.ext.asyncio import AsyncSession


from utils.error_response import ErrorResponse
from utils.database import get_db

from .schema import UserLoginResponseSchema, UserLoginSchema, UserSchema,UserCreateSchema
from .service import UserService

router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"model": ErrorResponse}},
)

@router.get("/health")
async def health():
    return {"message": "Up"}


@router.post('/',response_model=UserSchema)
async def create_user(request:Request,user:UserCreateSchema,db:AsyncSession=Depends(get_db)):

    service = UserService(db)
    user = await service.create_user(user)

    return user


@router.post('/login',response_model=UserLoginResponseSchema)
async def login(request:Request,user:UserLoginSchema,db:AsyncSession=Depends(get_db)):

    service = UserService(db)
    response = await service.login(user)

    return response