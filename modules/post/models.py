from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Text, Table, ForeignKey, Enum, func
from enum import Enum as PyEnum

from sqlalchemy.orm import relationship

from utils.database import Base

class PrivacyEnum(PyEnum):
    PUBLIC = "public"
    FOLLOWER = "follower"
    ONLY_ME = "only_me"

class ReactionTypeEnum(PyEnum):
    like = "like"
    love = "love"
    haha = "haha"
    wow = "wow"
    sad = "sad"
    angry = "angry"

post_media_association_table = Table(
    "post_media_association",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True),
    Column("media_id", Integer, ForeignKey("media.id", ondelete="CASCADE"), primary_key=True)
)

class Media(Base):
    __tablename__ = "media"
    id = Column(Integer, primary_key=True, index=True)
    file = Column(String(255), nullable=True)
    media_type = Column(String(50), nullable=True)
    tagged_in_posts = relationship("Post", secondary=post_media_association_table, back_populates="tagged_media")

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    content = Column(Text, nullable=True)
    privacy = Column(Enum(PrivacyEnum), default=PrivacyEnum.PUBLIC)
    original_post_id = Column(Integer, ForeignKey("posts.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=True, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="posts")
    original_post = relationship("Post", remote_side=[id], backref="shares")
    tagged_media = relationship("Media", secondary=post_media_association_table, back_populates="tagged_in_posts")
    reactions = relationship("Reaction", backref="post", cascade="all, delete-orphan")
    comments = relationship("Comment", backref="post" ,cascade="all, delete-orphan")

class Reaction(Base):
    __tablename__ = "reactions"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(Enum(ReactionTypeEnum, native_enum=False), nullable=False)

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="comments")
    replies = relationship("Comment", backref="parent", remote_side=[id])

