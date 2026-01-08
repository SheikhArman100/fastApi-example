from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session
from ...schemas.auth import LoginRequest, TokenResponse, RefreshTokenResponse, AuthUserResponse, ChangePasswordRequest, ForgetPasswordRequest, ResetPasswordRequest
from ...services.refresh_token_service import create_refresh_token as store_refresh_token, get_refresh_token_by_token, revoke_refresh_token, update_refresh_token
from ...services.user_service import change_password, forget_password, reset_password
from ...core.security import verify_password, create_access_token, create_refresh_token, parse_duration
from ...core.config import settings
from ...api.deps import get_db, auth
from ...models.user import User
from ...schemas.response import create_response
from ...services.file_service import get_file_by_id

router = APIRouter()


@router.post("/login")
async def login(
    user_credentials: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Login user and return access token with refresh token stored in database and cookie"""

    db_user = db.query(User).filter(User.email == user_credentials.email).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(user_credentials.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not db_user.is_active:
        raise HTTPException(status_code=401, detail="Account is deactivated")

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    access_token = create_access_token(
        data={"id": str(db_user.id), "email": db_user.email, "role": db_user.role.value}
    )

    refresh_token_value = create_refresh_token(
        data={"id": db_user.id, "email": db_user.email, "role": db_user.role.value}
    )

    store_refresh_token(
        db=db,
        user_id=db_user.id,
        token=refresh_token_value,
        ip_address=client_ip,
        user_agent=user_agent
    )

    refresh_token_expires = parse_duration(settings.refresh_token_expire_time)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token_value,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=int(refresh_token_expires.total_seconds())
    )

    return create_response(
        data={
            "access_token": access_token,
            "user": {
                "id": db_user.id,
                "name": db_user.name,
                "email": db_user.email,
                "role": db_user.role.value
            }
        },
        message="Login successful",
        status_code=200
    )

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Logout user by revoking refresh token from database and cookies"""

    # Check if refresh_token exists in cookies
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status_code=401, detail="Please sign in first")

    # Search database for the refresh token
    db_refresh_token = get_refresh_token_by_token(db, refresh_token)

    if not db_refresh_token:
        # Token not found in database, remove from cookies
        response.delete_cookie(
            key="refresh_token",
            httponly=True,
            secure=False,
            samesite="lax"
        )
        raise HTTPException(status_code=400, detail="RefreshToken not found")

    # Token found, revoke it from database
    revoke_refresh_token(db, refresh_token)

    # Remove refresh token from cookies
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=False,
        samesite="lax"
    )

    return create_response(
        message="Logout successful",
        status_code=200
    )

@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token from cookies"""

    # Get refresh token from cookies
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status_code=401, detail="Please sign in first")

    # Update tokens using the refresh token
    result = update_refresh_token(db, refresh_token)

    if not result:
        # Clear invalid refresh token from cookies
        response.delete_cookie(
            key="refresh_token",
            httponly=True,
            secure=False,
            samesite="lax"
        )
        raise HTTPException(status_code=401, detail="You are not authorized")
        

    # Calculate refresh token expiry for cookie max_age
    refresh_token_expires = parse_duration(settings.refresh_token_expire_time)

    # Set new refresh token in cookies
    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=int(refresh_token_expires.total_seconds())
    )

    return create_response(
        data={
            "access_token": result["access_token"],
            "role": result["role"]
        },
        message="Access token updated successfully",
        status_code=200
    )

@router.put("/change-password")
async def change_password_endpoint(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(auth()),
    db: Session = Depends(get_db)
):
    """Change user password"""

   
    change_password(
            db=db,
            user_id=current_user.id,
            current_password=password_data.current_password,
            new_password=password_data.new_password,
            current_user=current_user
        )

    return create_response(
            data=None,
            message="Password changed successfully",
            status_code=200
    )

@router.post("/forget-password")
async def forget_password_endpoint(
    forget_data: ForgetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Send forget password email with reset link"""

   
    result = forget_password(db, forget_data.email)
    return create_response(
            data=result,
            message="Password reset email sent successfully",
            status_code=200
    )
    

@router.post("/reset-password")
async def reset_password_endpoint(
    reset_data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Reset password using forget password token"""

    
    result = reset_password(db, reset_data.token, reset_data.new_password)
    return create_response(
            data=result,
            message="Password reset successfully",
            status_code=200
        )
    
    

@router.get("/user")
async def get_auth_user(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),  
):
    """Get authenticated user info using refresh token from cookies"""

    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Please sign in first")
    
    db_refresh_token = get_refresh_token_by_token(db, refresh_token)
    if not db_refresh_token:
        response.delete_cookie(
            key="refresh_token",
            httponly=True,
            secure=False,
            samesite="lax"
        )
        raise HTTPException(status_code=401, detail="You are not authorized")
    db_user = db.query(User).filter(User.id == db_refresh_token.user_id).first()
    if not db_user:
        response.delete_cookie(
            key="refresh_token",
            httponly=True,
            secure=False,
            samesite="lax"
        )
        raise HTTPException(status_code=401, detail="You are not authorized")
    
    # get user profile image
    # Get profile image details if exists
    db_profile_image = None
    if db_user.profile_image_id:
        file_record = get_file_by_id(db, db_user.profile_image_id)
        if file_record:
            db_profile_image = {
                "id": file_record.id,
                "path": file_record.path,
                "type": file_record.type,
                "original_name": file_record.original_name,
                "modified_name": file_record.modified_name
            }

    return create_response(
        data={
            "id": db_user.id,
            "name": db_user.name,
            "email": db_user.email,
            "role": db_user.role.value,
            "profile_image": db_profile_image
        },
        message="User fetched successfully",
        status_code=200
    )