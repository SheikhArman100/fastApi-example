from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response, Request
from sqlalchemy.orm import Session
from datetime import timedelta
from ...schemas.user import UserResponse, UserLogin
from ...schemas.token import Token
from ...services.file_service import save_file
from ...services.refresh_token_service import create_refresh_token as store_refresh_token, get_refresh_token_by_token, revoke_refresh_token, update_refresh_token
from ...core.security import hash_password, verify_password, create_access_token, create_refresh_token, parse_duration
from ...core.config import settings
from ...api.deps import get_db, auth
from ...models.user import User
from ...schemas.response import create_response

router = APIRouter()

@router.post("/register")
async def register(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    profile_image: UploadFile = File(...),
    current_user: User = Depends(auth("admin")),  # Only admins can register users
    db: Session = Depends(get_db)
):
    # Check if email already exists
    db_user = db.query(User).filter(User.email == email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Save the profile image in users module directory
    file_id = save_file(db, profile_image, module="users")

    # Hash the password
    hashed_password = hash_password(password)

    # Create the user record
    db_user = User(
        name=name,
        email=email,
        password=hashed_password,
        profile_image_id=file_id,
        created_by=current_user.id,  # Set creator as the admin user
        updated_by=current_user.id   # Set updater as the admin user
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return create_response(
        data={
            
                "id": db_user.id,
                "name": db_user.name,
                "email": db_user.email,
                "role": db_user.role.value,
                "is_active": db_user.is_active
            
        },
        message="User registered successfully",
        status_code=201 
    )

@router.post("/login")
async def login(
    user_credentials: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Login user and return access token with refresh token stored in database and cookie"""

    # Find user by email
    db_user = db.query(User).filter(User.email == user_credentials.email).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Verify password
    if not verify_password(user_credentials.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Check if user is active
    if not db_user.is_active:
        raise HTTPException(status_code=401, detail="Account is deactivated")

    # Get client information
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # Create tokens (using env-configured expiry times)
    access_token = create_access_token(
        data={"id": str(db_user.id), "email": db_user.email, "role": db_user.role.value}
    )

    refresh_token_value = create_refresh_token(
        data={"id": db_user.id, "email": db_user.email, "role": db_user.role.value}
    )

    # Store refresh token in database
    store_refresh_token(
        db=db,
        user_id=db_user.id,
        token=refresh_token_value,
        ip_address=client_ip,
        user_agent=user_agent
    )

    # Calculate refresh token expiry for cookie max_age
    refresh_token_expires = parse_duration(settings.refresh_token_expire_time)

    # Set refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token_value,
        httponly=True,  # Prevents JavaScript access
        secure=False,   # Set to True in production with HTTPS
        samesite="lax",
        max_age=int(refresh_token_expires.total_seconds())
    )

    # Return access token in response
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
    
    print("Refresh token from cookie:", refresh_token)

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
