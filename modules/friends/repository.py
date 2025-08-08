
from datetime import datetime, timezone
from .models import Friends
from sqlalchemy import delete, select


async def follow(db,user_id,follower_id):
    friend = Friends(user_id=user_id,friend_id=follower_id)
    db.add(friend)
    await db.commit()
    return True

async def unfollow(db,user_id,follower_id):
    await db.execute(delete(Friends).where(Friends.user_id == user_id).where(Friends.friend_id == follower_id))
    await db.commit()
    return True

async def toggle_follow(db,user_id,follower_id):
    friend = (await db.execute(select(Friends).where(Friends.user_id == user_id).where(Friends.friend_id == follower_id))).first()
    if friend:
        return await unfollow(db,user_id,follower_id)
    else:
        return await follow(db,user_id,follower_id)