from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response, Request
from sqlalchemy.orm import Session
from datetime import timedelta
from ...schemas.user import UserResponse, UserLogin
from ...schemas.token import Token
from ...services.file_service import save_file
from ...services.refresh_token_service import create_refresh_token as store_refresh_token
from ...core.security import hash_password, verify_password, create_access_token, create_refresh_token, parse_duration
from ...core.config import settings
from ...api.deps import get_db, auth
from ...models.user import User
from ...schemas.response import create_response

router = APIRouter()

@router.post("/register", response_model=UserResponse)
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

    return db_user

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
        data={"id": str(db_user.id), "email": db_user.email, "role": db_user.role.value}
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
