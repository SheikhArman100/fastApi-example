from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class CreateSessionRequest(BaseModel):
    """Request model for creating a new AI session"""
    title: Optional[str] = Field(None, description="Optional title for the session")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "My AI Chat Session"
            }
        }

class AskQuestionRequest(BaseModel):
    """Request model for asking a question to AI"""
    question: str = Field(..., min_length=1, max_length=2000, description="The question to ask AI")

    class Config:
        json_schema_extra = {
            "example": {
                "question": "What is the capital of France?"
            }
        }

class AIQuestionAnswerPair(BaseModel):
    """Response model for Q&A pairs"""
    question_id: str
    question: str
    question_created_at: datetime
    answer: Optional[str]
    answer_created_at: Optional[datetime]

class AISessionResponse(BaseModel):
    """Response model for AI session"""
    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    question_count: Optional[int] = Field(None, description="Number of questions in session")

class AISessionDetailResponse(BaseModel):
    """Detailed response for AI session with Q&A pairs"""
    session: AISessionResponse
    qa_pairs: List[AIQuestionAnswerPair]

class AIResponse(BaseModel):
    """Response model for AI answers"""
    question_id: str
    answer: str

class SessionsListResponse(BaseModel):
    """Response model for listing user sessions"""
    sessions: List[AISessionResponse]
