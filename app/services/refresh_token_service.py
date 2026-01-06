from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..models.refresh_token import RefreshToken
from ..core.security import parse_duration
from ..core.config import settings

def create_refresh_token(
    db: Session,
    user_id: int,
    token: str,
    ip_address: str = None,
    user_agent: str = None
) -> RefreshToken:
    """Create and store a refresh token in the database"""

    # Calculate expiry time
    expires_delta = parse_duration(settings.refresh_token_expire_time)
    expires_at = datetime.utcnow() + expires_delta

    # Create refresh token record
    refresh_token = RefreshToken(
        token=token,
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent,
        user_id=user_id,
        is_revoked=0
    )

    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)

    return refresh_token

def get_refresh_token_by_token(db: Session, token: str) -> RefreshToken:
    """Get refresh token by token string"""
    return db.query(RefreshToken).filter(RefreshToken.token == token).first()

def revoke_refresh_token(db: Session, token: str) -> bool:
    """Revoke a refresh token"""
    refresh_token = get_refresh_token_by_token(db, token)
    if refresh_token:
        refresh_token.is_revoked = 1
        refresh_token.updated_at = datetime.utcnow()
        db.commit()
        return True
    return False

def revoke_all_user_tokens(db: Session, user_id: int) -> int:
    """Revoke all refresh tokens for a user (useful for logout from all devices)"""
    tokens_revoked = db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.is_revoked == 0
    ).update({
        "is_revoked": 1,
        "updated_at": datetime.utcnow()
    })

    db.commit()
    return tokens_revoked

def cleanup_expired_tokens(db: Session) -> int:
    """Clean up expired refresh tokens (maintenance function)"""
    expired_count = db.query(RefreshToken).filter(
        RefreshToken.expires_at < datetime.utcnow()
    ).delete()

    db.commit()
    return expired_count

def get_user_active_tokens(db: Session, user_id: int) -> list[RefreshToken]:
    """Get all active refresh tokens for a user"""
    return db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.is_revoked == 0,
        RefreshToken.expires_at > datetime.utcnow()
    ).all()

def update_refresh_token(db: Session, old_token: str) -> dict:
    """Update access token using refresh token"""
    from ..core.security import verify_token, create_access_token, create_refresh_token
    from ..models.user import User

    # Find refresh token in database
    db_refresh_token = get_refresh_token_by_token(db, old_token)
    

    if not db_refresh_token:
        return None

    # Check if token is active
    if not db_refresh_token.is_active():
        return None

    # Verify the JWT token
    payload = verify_token(old_token, settings.refresh_token_secret)
    if not payload:
        return None

    # Check if token belongs to correct user
    token_user_id = payload.get("id")
    if str(db_refresh_token.user_id) != str(token_user_id):
        return None

    # Get user from database
    user = db.query(User).filter(User.id == db_refresh_token.user_id).first()
    if not user or not user.is_active:
        return None

    # Create new tokens
    new_access_token = create_access_token(
        data={"id": str(user.id), "email": user.email, "role": user.role.value}
    )

    new_refresh_token_value = create_refresh_token(
        data={"id": user.id, "email": user.email, "role": user.role.value}
    )

    # Update refresh token in database
    db_refresh_token.token = new_refresh_token_value
    db_refresh_token.updated_at = datetime.utcnow()
    db.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token_value,
        "role": user.role.value
    }
