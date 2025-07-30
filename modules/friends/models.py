from sqlalchemy import Column, Integer

from utils.database import Base


class Friends(Base):
    __tablename__ = "friends"

    user_id = Column(Integer, primary_key=True, index=True)
    friend_id = Column(Integer, primary_key=True, index=True)