
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, Request
from typing import List, Optional
from ..db.session import SessionLocal
from ..core.security import verify_token
from ..models.user import User
from ..core.config import settings
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token
    """
    # Get authorization header
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")

    token = auth_header.split(" ")[1]

    # Verify token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Get user from database
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account is deactivated")

    return user

def auth(*required_roles: str):
    """
    Authentication dependency that verifies JWT token and checks user roles.

    Usage:
        @app.get("/protected")
        async def protected_route(user: User = Depends(auth("admin", "user"))):
            return {"message": "Access granted"}

        @app.get("/admin-only")
        async def admin_route(user: User = Depends(auth("admin"))):
            return {"message": "Admin access granted"}
    """
    def auth_dependency(
        request: Request,
        db: Session = Depends(get_db)
    ) -> User:
        try:
            # Get authorization header
            auth_header = request.headers.get("authorization") or request.headers.get("Authorization")

            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(status_code=403, detail="You are not authorized")

            token = auth_header.split(" ")[1]

            # Verify token
            payload = verify_token(token,settings.access_token_secret)
            if not payload:
                raise HTTPException(status_code=403, detail="You are not authorized")

            # Get user from database
            user_id = payload.get("id")
            if not user_id:
                raise HTTPException(status_code=403, detail="You are not authorized")

            user = db.query(User).filter(User.id == int(user_id)).first()
            if not user:
                raise HTTPException(status_code=403, detail="You are not authorized")

            if not user.is_active:
                raise HTTPException(status_code=401, detail="Account is deactivated")

            # Role guard
            if required_roles and user.role.value not in required_roles:
                raise HTTPException(status_code=403, detail="You have no access")

            return user

        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=403, detail="You are not authorized")

    return auth_dependency

# Stub dependency for get_current_admin (keeping for backward compatibility)
def get_current_admin(db: Session = Depends(get_db)):
    # This can now use the auth dependency above
    pass
