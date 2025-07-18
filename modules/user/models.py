from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime,Date,Text
from sqlalchemy.orm import relationship
from utils.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String,nullable=True)
    email = Column(String, unique=True)
    password = Column(String)
    is_active = Column(Boolean, default=True)
 
    profile_image = Column(String, nullable=True)
    cover_image = Column(String, nullable=True)

    birthdate = Column(Date, nullable=True)
    gender = Column(String, nullable=True)
    bio = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)



class Setting(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    key = Column(String)
    value = Column(String)
    user = relationship("User")