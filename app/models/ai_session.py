from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.base import Base
import uuid

class AISession(Base):
    __tablename__ = "ai_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=True)  # Auto-generated or user-defined title
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="ai_sessions")
    questions = relationship("AIQuestion", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AISession(id={self.id}, title={self.title}, user_id={self.user_id})>"

class AIQuestion(Base):
    __tablename__ = "ai_questions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("ai_sessions.id"), nullable=False)
    question = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("AISession", back_populates="questions")
    answer = relationship("AIAnswer", back_populates="question", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AIQuestion(id={self.id}, session_id={self.session_id})>"

class AIAnswer(Base):
    __tablename__ = "ai_answers"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(String(36), ForeignKey("ai_questions.id"), nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    question = relationship("AIQuestion", back_populates="answer")

    def __repr__(self):
        return f"<AIAnswer(id={self.id}, question_id={self.question_id})>"
