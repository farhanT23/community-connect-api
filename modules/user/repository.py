
from datetime import datetime, timezone
from modules.user.models import User
from sqlalchemy import select



def create_object(user):
    obj = User(name=user.name,email=user.email,password=user.password)

    if(hasattr(user,"is_active")):
        obj.is_active = user.is_active

    if(hasattr(user,"is_active")):
        obj.created_at = user.created_at
    if(hasattr(user,"is_active")):
        obj.updated_at = user.updated_at
    return obj

async def get_all(db):
    result =  await db.execute(select(User))

    return result.scalars().all()

async def get_by_id(db,user_id):
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    return result.scalars().first()


async def get_by_email(db,email):
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    return result.scalars().first()

async def create(db,user):

    if(user.is_active == None):
        user.is_active = True

    if(user.created_at == None):
        user.created_at = datetime.now(timezone.utc)
    if(user.updated_at == None):
        user.updated_at = datetime.now(timezone.utc)
    try:
        db.add(user)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise e
    await db.refresh(user)
    return user

async def delete(user_id,db):
    await db.query(User).filter(User.id == user_id).delete()
    await db.commit()
    return True

