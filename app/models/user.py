from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from ..db.base import Base
from datetime import datetime

class Role(str, enum.Enum):
    admin = "admin"
    user = "user"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(Role), default=Role.user)
    profile_image_id = Column(Integer, ForeignKey("files.id"))
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    profile_image = relationship("File")
    refresh_tokens = relationship("RefreshToken", back_populates="user")
    ai_sessions = relationship("AISession", back_populates="user")
    creator = relationship("User", remote_side=[id], foreign_keys=[created_by])
    updater = relationship("User", remote_side=[id], foreign_keys=[updated_by])
