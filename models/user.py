# app/models/user.py

from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from app.database.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # Personal info
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    birthdate = Column(Date, nullable=False)
    gender = Column(String(1), nullable=False)  # Choices: M/F

    # Auth
    password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_email_verified = Column(Boolean, default=False)

    # Profile media
    profile_image_id = Column(Integer, ForeignKey("media.id"), nullable=True)
    cover_image_id = Column(Integer, ForeignKey("media.id"), nullable=True)

    profile_image = relationship("Media", foreign_keys=[profile_image_id], backref="users_with_profile_image")
    cover_image = relationship("Media", foreign_keys=[cover_image_id], backref="users_with_cover_image")

    # Profile details
    bio = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    followers = relationship(
        "Follow",
        foreign_keys="Follow.following_id",
        back_populates="following_user",
        cascade="all, delete-orphan"
    )

    following = relationship(
        "Follow",
        foreign_keys="Follow.follower_id",
        back_populates="follower_user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(name={self.name}, email={self.email})>"
