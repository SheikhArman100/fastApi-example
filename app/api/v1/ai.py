from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from ...schemas.ai import (
    CreateSessionRequest, AskQuestionRequest, AISessionResponse,
    AISessionDetailResponse, AIResponse, SessionsListResponse
)
from ...services.ai_service import (
    create_ai_session, get_user_sessions, get_session_with_questions,
    delete_ai_session, ask_gemini_with_context
)
from ...api.deps import get_db, auth
from ...models.user import User
from ...schemas.response import create_response

router = APIRouter()

@router.post("/sessions", response_model=AISessionResponse, summary="Create AI Session", description="Create a new AI chat session")
async def create_session(
    session_data: CreateSessionRequest,
    current_user: User = Depends(auth()),
    db: Session = Depends(get_db)
):
    """Create a new AI chat session"""

    try:
        session = create_ai_session(db, current_user.id, session_data.title)

        return create_response(
            data={
                "id": session.id,
                "title": session.title,
                "created_at": session.created_at,
                "updated_at": session.updated_at
            },
            message="AI session created successfully",
            status_code=201
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sessions", summary="List Sessions", description="Get all AI sessions for the authenticated user")
async def list_sessions(
    current_user: User = Depends(auth()),
    db: Session = Depends(get_db)
):
    """Get all AI sessions for the current user"""

    try:
        sessions = get_user_sessions(db, current_user.id)

        session_list = []
        for session_data in sessions:
            session = session_data["session"]
            question_count = session_data["question_count"]

            session_list.append({
                "id": session.id,
                "title": session.title,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
                "question_count": question_count
            })

        return create_response(
            data={"sessions": session_list},
            message="Sessions retrieved successfully",
            status_code=200
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sessions/{session_id}", summary="Get Session Details", description="Get detailed information about a specific AI session including all Q&A pairs")
async def get_session(
    session_id: str,
    current_user: User = Depends(auth()),
    db: Session = Depends(get_db)
):
    """Get a specific AI session with all its Q&A pairs"""

    try:
        session_data = get_session_with_questions(db, session_id, current_user.id)

        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        session = session_data["session"]
        qa_pairs = session_data["qa_pairs"]

        return create_response(
            data={
                "session": {
                    "id": session.id,
                    "title": session.title,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                    "question_count": len(qa_pairs)
                },
                "qa_pairs": qa_pairs
            },
            message="Session details retrieved successfully",
            status_code=200
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/ask", summary="Ask AI Question", description="Ask a question to Gemini AI. If no session_id provided, creates a new session automatically.")
async def ask_question(
    question_data: AskQuestionRequest,
    session_id: Optional[str] = None,
    current_user: User = Depends(auth()),
    db: Session = Depends(get_db)
):
    """Ask a question to Gemini AI with conversation context"""

    try:
        result = ask_gemini_with_context(
            db, session_id, current_user.id, question_data.question
        )

        if result is None:
            raise HTTPException(status_code=404, detail="Session not found or access denied")

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return create_response(
            data={
                "question_id": result["question_id"],
                "answer": result["answer"],
                "session_id": session_id
            },
            message="AI response generated successfully",
            status_code=200
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

@router.delete("/sessions/{session_id}", summary="Delete AI Session", description="Delete an AI session and all its messages")
async def delete_session(
    session_id: str,
    current_user: User = Depends(auth()),
    db: Session = Depends(get_db)
):
    """Delete an AI session"""

    try:
        deleted = delete_ai_session(db, session_id, current_user.id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Session not found")

        return create_response(
            data=None,
            message="Session deleted successfully",
            status_code=200
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
