import google.genai as genai
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from ..models.ai_session import AISession, AIQuestion, AIAnswer
from ..models.user import User
from ..core.config import settings
from ..core.security import hash_password, verify_password
import uuid

# Configure Gemini API
client = genai.Client(api_key=settings.google_api_key)

def create_ai_session(db: Session, user_id: int, title: Optional[str] = None) -> AISession:
    """Create a new AI chat session for a user"""

    session = AISession(
        user_id=user_id,
        title=title or "New Chat Session"
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session

def get_user_sessions(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """Get all AI sessions for a user with question counts"""

    sessions = db.query(AISession).filter(AISession.user_id == user_id).order_by(AISession.created_at.desc()).all()

    session_list = []
    for session in sessions:
        # Count questions in session
        question_count = db.query(AIQuestion).filter(AIQuestion.session_id == session.id).count()

        session_list.append({
            "session": session,
            "question_count": question_count
        })

    return session_list

def get_session_with_questions(db: Session, session_id: str, user_id: int) -> Optional[Dict[str, Any]]:
    """Get a session with all its questions and answers, ensuring user owns the session"""

    session = db.query(AISession).filter(
        AISession.id == session_id,
        AISession.user_id == user_id
    ).first()

    if not session:
        return None

    # Get questions with their answers
    questions = db.query(AIQuestion).filter(
        AIQuestion.session_id == session_id
    ).order_by(AIQuestion.created_at.asc()).all()

    # Build question-answer pairs
    qa_pairs = []
    for question in questions:
        qa_pairs.append({
            "question_id": question.id,
            "question": question.question,
            "question_created_at": question.created_at,
            "answer": question.answer.answer if question.answer else None,
            "answer_created_at": question.answer.created_at if question.answer else None
        })

    return {
        "session": session,
        "qa_pairs": qa_pairs
    }

def delete_ai_session(db: Session, session_id: str, user_id: int) -> bool:
    """Delete an AI session and all its questions/answers"""

    session = db.query(AISession).filter(
        AISession.id == session_id,
        AISession.user_id == user_id
    ).first()

    if not session:
        return False

    db.delete(session)
    db.commit()

    return True

def ask_gemini_with_context(db: Session, session_id: Optional[str], user_id: int, question: str) -> Optional[Dict[str, Any]]:
    """Ask Gemini a question with conversation context from the session"""

    # If no session_id provided, create a new session
    if session_id is None:
        session = create_ai_session(db, user_id, "New Chat Session")
        session_id = session.id
    else:
        # Verify session ownership
        session = db.query(AISession).filter(
            AISession.id == session_id,
            AISession.user_id == user_id
        ).first()

        if not session:
            return None

    try:
        # Build conversation history from previous Q&A pairs
        conversation_history = []

        # Get all previous questions and answers for context
        previous_qas = db.query(AIQuestion).filter(
            AIQuestion.session_id == session_id
        ).order_by(AIQuestion.created_at.asc()).all()

        for qa in previous_qas:
            if qa.answer:  # Only include completed Q&A pairs
                conversation_history.append(f"User: {qa.question}")
                conversation_history.append(f"Assistant: {qa.answer.answer}")

        # Add current question
        conversation_history.append(f"User: {question}")

        # Create prompt with context (last 20 exchanges for context)
        context = "\n".join(conversation_history[-20:])
        prompt = f"""You are a helpful AI assistant. Here's the conversation history:

{context}

Please provide a helpful and accurate response to the user's latest question."""

        # Generate response using new Google GenAI SDK
        print(f"DEBUG: Making Gemini API call for session {session_id}")
        response = client.models.generate_content(
            model='models/gemini-2.0-flash',
            contents=prompt
        )
        print(f"DEBUG: Gemini API call completed")
        ai_response = response.candidates[0].content.parts[0].text
        print(f"DEBUG: Response extracted, length: {len(ai_response)}")

        # Create question record
        question_record = AIQuestion(
            session_id=session_id,
            question=question
        )
        db.add(question_record)
        db.flush()  # Get the question ID

        # Create answer record linked to question
        answer_record = AIAnswer(
            question_id=question_record.id,
            answer=ai_response
        )
        db.add(answer_record)

        # Update session timestamp
        session.updated_at = db.func.now()

        db.commit()

        return {
            "question_id": question_record.id,
            "answer": ai_response
        }

    except Exception as e:
        print(f"Gemini API Error: {e}")
        db.rollback()
        return {
            "error": f"Sorry, I encountered an error: {str(e)}"
        }

def generate_session_title(db: Session, session_id: str) -> str:
    """Generate a title for the session based on first question"""

    first_question = db.query(AIQuestion).filter(
        AIQuestion.session_id == session_id
    ).order_by(AIQuestion.created_at.asc()).first()

    if not first_question:
        return "New Chat Session"

    # Use first few words of the first question as title
    content = first_question.question[:50].strip()
    if len(content) < 50:
        return content
    else:
        return content + "..."
