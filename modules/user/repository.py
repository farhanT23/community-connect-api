
from datetime import datetime, timezone
from modules.user.models import User
from sqlalchemy import case, func, select
from sqlalchemy.orm import aliased
from ..friends.models import Friends



def create_object(user):
    obj = User(name=user.name,email=user.email,password=user.password)

    if(hasattr(user,"is_active")):
        obj.is_active = user.is_active

    if(hasattr(user,"birthdate")):
        obj.birthdate = user.birthdate

    if(hasattr(user,"gender")):
        obj.gender = user.gender

    if(hasattr(user,"is_active")):
        obj.created_at = user.created_at
    if(hasattr(user,"is_active")):
        obj.updated_at = user.updated_at
    return obj

from sqlalchemy import select, case, func
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession

async def get_all(db: AsyncSession, user_id: int | None = None):
    statement = select(User)

    if user_id:
        f = aliased(Friends)
        statement = (
            select(
                User,
                case(
                    (f.friend_id != None, True),
                    else_=False
                ).label("is_followed")
            )
            .outerjoin(f, (f.friend_id == User.id) & (f.user_id == user_id))
            .filter(User.id != user_id)
            .order_by(func.random())
            .limit(20)
        )

    result = await db.execute(statement)

    if user_id:
        # Unpack the (User, is_followed) tuples
        data = []
        for user, is_followed in result.all():
            user.is_followed = is_followed
            data.append(user)
    else:
        data = result.scalars().all()

    return data


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

async def update(db,user):
    user.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)
    return user


async def get_by_id_details(db, user_id: int, current_user_id: int | None = None):
    # Subqueries for counts
    followers_count = (
        select(func.count(Friends.user_id))
        .where(Friends.friend_id == user_id)
        .scalar_subquery()
    )

    following_count = (
        select(func.count(Friends.friend_id))
        .where(Friends.user_id == user_id)
        .scalar_subquery()
    )

    if current_user_id:
        f = aliased(Friends)
        query = (
            select(
                User,
                case(
                    (f.friend_id != None, True),
                    else_=False
                ).label("is_followed"),
                followers_count.label("followers_count"),
                following_count.label("following_count")
            )
            .outerjoin(f, (f.friend_id == User.id) & (f.user_id == current_user_id))
            .where(User.id == user_id)
        )

        result = await db.execute(query)
        user_row = result.first()
        if user_row:
            user, is_followed, followers_count, following_count = user_row
            user.is_followed = is_followed
            user.followers_count = followers_count
            user.following_count = following_count
            return user
        return None
    else:
        query = (
            select(
                User,
                followers_count.label("followers_count"),
                following_count.label("following_count")
            )
            .where(User.id == user_id)
        )
        result = await db.execute(query)
        user_row = result.first()
        if user_row:
            user, followers_count, following_count = user_row
            user.followers_count = followers_count
            user.following_count = following_count
            return user
        return None
    

async def get_user_followers(db,user_id:int,current_id:int|None=None):
    simple_query = select(Friends.user_id).where(Friends.friend_id == user_id).subquery()

    if current_id:
        f = aliased(Friends)
        query = (
            select(
                User,
                case(
                    (f.friend_id != None, True),
                    else_=False
                ).label("is_followed")
            )
            .outerjoin(f, (f.friend_id == User.id) & (f.user_id == current_id))
            .where(User.id.in_(simple_query))
        )
        result = await db.execute(query)
        if current_id:
        # Unpack the (User, is_followed) tuples
            data = []
            for user, is_followed in result.all():
                user.is_followed = is_followed
                data.append(user)
            return data
    else:
        query = select(User).where(User.id.in_(simple_query))
        result = await db.execute(query)
        return result.scalars().all()
    


async def get_user_following(db,user_id:int,current_id:int|None=None):
    simple_query = select(Friends.friend_id).where(Friends.user_id == user_id).subquery()

    if current_id:
        f = aliased(Friends)
        query = (
            select(
                User,
                case(
                    (f.friend_id != None, True),
                    else_=False
                ).label("is_followed")
            )
            .outerjoin(f, (f.friend_id == User.id) & (f.user_id == current_id))
            .where(User.id.in_(simple_query))
        )
        result = await db.execute(query)
        if current_id:
        # Unpack the (User, is_followed) tuples
            data = []
            for user, is_followed in result.all():
                user.is_followed = is_followed
                data.append(user)
            return data
    else:
        query = select(User).where(User.id.in_(simple_query))
        result = await db.execute(query)
        return result.scalars().all()
    
async def get_all_user_by_name_alike(db: AsyncSession, name: str):
    query = select(User).where(User.name.ilike(f"%{name}%"))
    result = await db.execute(query)

    return result.scalars().all()
